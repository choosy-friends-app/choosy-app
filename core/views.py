import json
from datetime import datetime, timedelta

from django.contrib.auth import get_user_model
from django.contrib.auth import authenticate, login, logout
from django.core.exceptions import PermissionDenied
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt

from .models import Group, GroupMember, Plan, PlanProposal, Vote

User = get_user_model()


def _default_voting_end():
    return timezone.now() + timedelta(hours=24)


def _parse_voting_end(request):
    date_value = (request.POST.get("voting_end_date") or "").strip()
    time_value = (request.POST.get("voting_end_time") or "").strip()
    if not date_value:
        return _default_voting_end()

    if not time_value:
        time_value = "21:00"

    naive_dt = datetime.fromisoformat(f"{date_value}T{time_value}")
    end_dt = timezone.make_aware(naive_dt, timezone.get_current_timezone())
    if end_dt <= timezone.now():
        raise ValueError("La fecha de cierre debe estar en el futuro.")
    return end_dt


def _user_groups_queryset(request):
    if request.user.is_authenticated:
        return Group.objects.filter(
            Q(owner=request.user)
            | Q(members__user=request.user, members__status=GroupMember.Status.ACTIVE)
        ).distinct()
    return Group.objects.all()


def _seed_demo_groups():
    if Group.objects.exists():
        return
    Group.objects.create(name="The Foodies Collective", description="Culinary adventures")
    Group.objects.create(name="Adventure Seekers", description="Outdoor stuff")


def _decorate_plan_option(plan):
    votes = list(plan.votes.select_related("member", "user").order_by("-created_at"))
    plan.upvote_count = sum(1 for vote in votes if vote.value > 0)
    plan.downvote_count = sum(1 for vote in votes if vote.value < 0)
    plan.vote_score = plan.upvote_count - plan.downvote_count
    plan.vote_count = len(votes)
    plan.recent_voters = [
        vote.member.display_name if vote.member else (vote.user.username if vote.user else "Guest")
        for vote in votes[:4]
    ]
    return plan


def _close_proposal(proposal):
    proposal = _decorate_proposal(proposal)
    if proposal is None or proposal.status != PlanProposal.Status.VOTING:
        return proposal

    leading_option = proposal.leading_option
    if leading_option is not None:
        leading_option.status = Plan.Status.CHOSEN
        leading_option.save(update_fields=["status"])
        proposal.chosen_plan = leading_option
        proposal.status = PlanProposal.Status.CHOSEN
        proposal.group.status = Group.Status.ACTIVE
        proposal.group.save(update_fields=["status"])
    else:
        proposal.status = PlanProposal.Status.CANCELLED
        proposal.group.status = Group.Status.PLANNING
        proposal.group.save(update_fields=["status"])

    proposal.save(update_fields=["status", "chosen_plan"])
    return _decorate_proposal(proposal)


def _sync_proposal_status(proposal):
    if proposal is None:
        return None
    if proposal.status == PlanProposal.Status.VOTING and proposal.voting_ends_at and proposal.voting_ends_at <= timezone.now():
        return _close_proposal(proposal)
    return _decorate_proposal(proposal)


def _decorate_proposal(proposal):
    if proposal is None:
        return None

    options = [_decorate_plan_option(plan) for plan in proposal.plans.order_by("option_order", "created_at")]
    proposal.options = options
    proposal.option_count = len(options)
    proposal.total_votes = sum(option.vote_count for option in options)
    proposal.leading_option = max(
        options,
        key=lambda option: (option.vote_score, option.upvote_count, -option.option_order),
        default=None,
    )
    proposal.recent_votes = list(
        Vote.objects.filter(plan__proposal=proposal)
        .select_related("plan", "member", "user")
        .order_by("-created_at")[:5]
    )
    active_members = list(proposal.group.members.filter(status=GroupMember.Status.ACTIVE))
    proposal.expected_voter_count = len(active_members)
    completed_voters = []
    partial_voters = []

    for member in active_members:
        member_vote_count = Vote.objects.filter(plan__proposal=proposal, member=member).count()
        if member_vote_count >= proposal.option_count and proposal.option_count > 0:
            completed_voters.append(member.display_name)
        elif member_vote_count > 0:
            partial_voters.append(member.display_name)

    proposal.completed_voters = completed_voters
    proposal.partial_voters = partial_voters
    proposal.pending_voters = [
        member.display_name
        for member in active_members
        if member.display_name not in completed_voters and member.display_name not in partial_voters
    ]
    proposal.completed_voter_count = len(completed_voters)
    proposal.is_closed = proposal.status in {PlanProposal.Status.CHOSEN, PlanProposal.Status.CANCELLED}
    return proposal


def _decorate_proposal_for_user(proposal, user):
    proposal = _decorate_proposal(proposal)
    if proposal is None:
        return None

    vote_map = {}
    voted_option_ids = set()
    voted_option_count = 0

    if user and user.is_authenticated:
        member = proposal.group.members.filter(user=user, status=GroupMember.Status.ACTIVE).first()
        if member is not None:
            votes = Vote.objects.filter(plan__proposal=proposal, member=member).select_related("plan")
            for vote in votes:
                vote_map[vote.plan_id] = vote.value
                voted_option_ids.add(vote.plan_id)
            voted_option_count = len(vote_map)

    proposal.current_user_vote_map = vote_map
    proposal.current_user_voted_option_ids = voted_option_ids
    proposal.current_user_voted_option_count = voted_option_count
    proposal.current_user_completed = proposal.option_count > 0 and voted_option_count >= proposal.option_count

    for option in proposal.options:
        option.current_user_vote = vote_map.get(option.id)

    return proposal


def _decorate_groups(groups, user=None):
    decorated = []
    for group in groups:
        members = list(group.members.filter(status=GroupMember.Status.ACTIVE)[:4])
        active_proposal = _decorate_proposal_for_user(
            _sync_proposal_status(
                group.proposals.filter(status=PlanProposal.Status.VOTING).order_by("-created_at").first()
            ),
            user,
        )
        group.member_count = group.members.filter(status=GroupMember.Status.ACTIVE).count()
        group.active_proposal = active_proposal
        group.voting_plans_count = active_proposal.option_count if active_proposal else 0
        group.preview_members = members
        group.extra_members_count = max(group.member_count - len(members), 0)
        decorated.append(group)
    return decorated


def _resolve_member(group, user):
    if group.owner_id == user.id:
        return group.add_member(user=user, role=GroupMember.Role.OWNER)

    member = group.members.filter(
        user=user,
        status=GroupMember.Status.ACTIVE,
    ).first()
    if member is None:
        raise PermissionDenied("You do not belong to this group.")
    return member


def _resolve_group_for_request(request, group_id):
    group = get_object_or_404(Group, id=group_id)
    if not request.user.is_authenticated:
        return group
    _resolve_member(group, request.user)
    return group


def _require_group_admin(group, user):
    member = _resolve_member(group, user)
    if not member.is_admin:
        raise PermissionDenied("You do not have permission to manage this group.")
    return member


def _vote_identity_for_request(request, plan):
    if request.user.is_authenticated:
        member = _resolve_member(plan.group, request.user)
        return {"user": request.user, "member": member, "session_key": ""}

    session_key = request.session.session_key
    if not session_key:
        request.session.save()
        session_key = request.session.session_key
    return {"user": None, "member": None, "session_key": session_key}


def _active_group_proposal(group):
    return _sync_proposal_status(group.proposals.filter(status=PlanProposal.Status.VOTING).order_by("-created_at").first())


def dashboard(request):
    user_groups = _user_groups_queryset(request)

    if not request.user.is_authenticated and not user_groups.exists():
        _seed_demo_groups()
        user_groups = _user_groups_queryset(request)

    user_groups = _decorate_groups(user_groups, request.user)
    recent_votes = (
        Vote.objects.select_related("plan", "plan__group", "member", "user")
        .order_by("-created_at")[:5]
    )

    return render(
        request,
        "pages/dashboard.html",
        {
            "meta_title": "Dashboard",
            "active_page": "dashboard",
            "topbar_context": "Dashboard",
            "groups": user_groups,
            "recent_votes": recent_votes,
        },
    )


def login_view(request):
    if request.user.is_authenticated:
        return redirect("dashboard")

    error_message = ""
    if request.method == "POST":
        username = (request.POST.get("username") or "").strip()
        password = request.POST.get("password") or ""
        user = authenticate(request, username=username, password=password)
        if user is None:
            error_message = "Usuario o password incorrectos."
        else:
            login(request, user)
            return redirect("dashboard")

    return render(
        request,
        "pages/login.html",
        {
            "meta_title": "Login",
            "active_page": "login",
            "topbar_context": "Login",
            "error_message": error_message,
        },
    )


def register_view(request):
    if request.user.is_authenticated:
        return redirect("dashboard")

    error_message = ""
    if request.method == "POST":
        username = (request.POST.get("username") or "").strip()
        password = request.POST.get("password") or ""
        password_confirm = request.POST.get("password_confirm") or ""

        if not username:
            error_message = "El username es obligatorio."
        elif User.objects.filter(username=username).exists():
            error_message = "Ese username ya existe."
        elif len(password) < 8:
            error_message = "La password debe tener al menos 8 caracteres."
        elif password != password_confirm:
            error_message = "Las passwords no coinciden."
        else:
            user = User.objects.create_user(
                username=username,
                password=password,
                first_name=(request.POST.get("first_name") or "").strip(),
                last_name=(request.POST.get("last_name") or "").strip(),
                email=(request.POST.get("email") or "").strip(),
            )
            login(request, user)
            return redirect("dashboard")

    return render(
        request,
        "pages/register.html",
        {
            "meta_title": "Register",
            "active_page": "register",
            "topbar_context": "Register",
            "error_message": error_message,
        },
    )


def logout_view(request):
    logout(request)
    return redirect("login")


def active_plans(request):
    user_groups = _user_groups_queryset(request)
    proposals = []

    if not request.user.is_authenticated and not user_groups.exists():
        _seed_demo_groups()
        user_groups = _user_groups_queryset(request)

    for group in user_groups:
        proposal = _decorate_proposal_for_user(_active_group_proposal(group), request.user)
        if proposal is not None:
            proposal.group = group
            proposals.append(proposal)

    proposals.sort(key=lambda proposal: proposal.updated_at, reverse=True)
    selected_proposal = None
    selected_id = request.GET.get("proposal")
    if selected_id:
        try:
            selected_id = int(selected_id)
        except (TypeError, ValueError):
            selected_id = None
        if selected_id is not None:
            selected_proposal = next((proposal for proposal in proposals if proposal.id == selected_id), None)

    hero_proposal = selected_proposal
    top_options = sorted(
        [option for proposal in proposals for option in proposal.options],
        key=lambda option: (option.vote_score, option.upvote_count, -option.option_order),
        reverse=True,
    )[:3]
    recent_votes = (
        Vote.objects.filter(plan__proposal__in=[proposal.id for proposal in proposals])
        .select_related("plan", "plan__proposal", "member", "user")
        .order_by("-created_at")[:5]
        if proposals
        else []
    )

    return render(
        request,
        "pages/active_plans.html",
        {
            "meta_title": "Active Plans",
            "active_page": "active_plans",
            "topbar_context": "Active Plans",
            "proposals": proposals,
            "hero_proposal": hero_proposal,
            "selected_proposal": hero_proposal,
            "top_options": top_options,
            "recent_votes": recent_votes,
        },
    )


def archive(request):
    return render(
        request,
        "pages/archive.html",
        {
            "meta_title": "Archive",
            "active_page": "archive",
            "topbar_context": "Archive",
        },
    )


def groups(request):
    user_groups = _user_groups_queryset(request)
    success_message = ""
    error_message = ""
    open_create_modal = False

    if not request.user.is_authenticated and not user_groups.exists():
        _seed_demo_groups()
        user_groups = _user_groups_queryset(request)

    if request.method == "POST":
        if not request.user.is_authenticated:
            error_message = "Necesitas iniciar sesion para crear grupos o invitar miembros."
        else:
            action = request.POST.get("action")
            try:
                if action == "create_group":
                    open_create_modal = True
                    name = (request.POST.get("name") or "").strip()
                    description = (request.POST.get("description") or "").strip()
                    if not name:
                        raise ValueError("El nombre del grupo es obligatorio.")
                    group = Group.objects.create(
                        name=name,
                        description=description,
                        owner=request.user,
                    )
                    group.add_member(user=request.user, role=GroupMember.Role.OWNER)
                    success_message = f"Grupo '{group.name}' creado correctamente."
                    open_create_modal = False
                elif action == "add_member":
                    group = _resolve_group_for_request(request, request.POST.get("group_id"))
                    _require_group_admin(group, request.user)
                    username = (request.POST.get("username") or "").strip()
                    if not username:
                        raise ValueError("Debes indicar un username para invitar.")
                    user = get_object_or_404(User, username=username)
                    member = group.add_member(
                        user=user,
                        display_name=request.POST.get("display_name", ""),
                        role=GroupMember.Role.MEMBER,
                        invited_by=request.user,
                    )
                    success_message = f"{member.display_name} ya forma parte de {group.name}."
                else:
                    error_message = "Accion no soportada."
            except PermissionDenied as exc:
                error_message = str(exc)
            except ValueError as exc:
                error_message = str(exc)

        user_groups = _user_groups_queryset(request)

    user_groups = _decorate_groups(user_groups, request.user)
    total_members = sum(group.member_count for group in user_groups)
    total_pending_votes = sum(group.voting_plans_count for group in user_groups)

    return render(
        request,
        "pages/groups.html",
        {
            "meta_title": "Groups",
            "active_page": "groups",
            "topbar_context": "Groups",
            "groups": user_groups,
            "total_groups": len(user_groups),
            "total_members": total_members,
            "total_pending_votes": total_pending_votes,
            "success_message": success_message,
            "error_message": error_message,
            "open_create_modal": open_create_modal,
        },
    )


@csrf_exempt
def api_create_group(request):
    if request.method != "POST":
        return JsonResponse({"status": "method_not_allowed"}, status=405)
    if not request.user.is_authenticated:
        return JsonResponse({"status": "error", "message": "Authentication required."}, status=403)

    try:
        data = json.loads(request.body or "{}")
        name = (data.get("name") or "").strip()
        description = (data.get("description") or "").strip()
        if not name:
            return JsonResponse({"status": "error", "message": "Group name is required."}, status=400)

        group = Group.objects.create(
            name=name,
            description=description,
            owner=request.user,
        )
        owner_member = group.add_member(user=request.user, role=GroupMember.Role.OWNER)
        return JsonResponse(
            {
                "status": "success",
                "group": {
                    "id": group.id,
                    "name": group.name,
                    "description": group.description,
                    "owner_member_id": owner_member.id,
                },
            },
            status=201,
        )
    except json.JSONDecodeError:
        return JsonResponse({"status": "error", "message": "Invalid JSON payload."}, status=400)


@csrf_exempt
def api_add_group_member(request, group_id):
    if request.method != "POST":
        return JsonResponse({"status": "method_not_allowed"}, status=405)
    if not request.user.is_authenticated:
        return JsonResponse({"status": "error", "message": "Authentication required."}, status=403)

    group = _resolve_group_for_request(request, group_id)

    try:
        _require_group_admin(group, request.user)
        data = json.loads(request.body or "{}")
        username = (data.get("username") or "").strip()
        role = data.get("role") or GroupMember.Role.MEMBER
        if role not in GroupMember.Role.values:
            return JsonResponse({"status": "error", "message": "Invalid role."}, status=400)
        if not username:
            return JsonResponse({"status": "error", "message": "Username is required."}, status=400)

        user = get_object_or_404(User, username=username)
        member = group.add_member(
            user=user,
            display_name=data.get("display_name", ""),
            role=role,
            invited_by=request.user,
        )
        return JsonResponse(
            {
                "status": "success",
                "member": {
                    "id": member.id,
                    "group_id": group.id,
                    "user_id": user.id,
                    "display_name": member.display_name,
                    "role": member.role,
                    "status": member.status,
                },
            },
            status=201,
        )
    except PermissionDenied as exc:
        return JsonResponse({"status": "error", "message": str(exc)}, status=403)
    except json.JSONDecodeError:
        return JsonResponse({"status": "error", "message": "Invalid JSON payload."}, status=400)


def start_new_plan(request):
    user_groups = _user_groups_queryset(request)
    default_voting_end = _default_voting_end()

    if not request.user.is_authenticated and not user_groups.exists():
        _seed_demo_groups()
        user_groups = _user_groups_queryset(request)

    if request.method == "POST":
        group_id = request.POST.get("group_id")
        global_title = request.POST.get("title")
        global_description = request.POST.get("description", "")
        created_by = request.user if request.user.is_authenticated else None

        options_data = request.POST.get("options_json", "[]")
        try:
            options = json.loads(options_data)
        except json.JSONDecodeError:
            options = []

        if not group_id:
            return render(
                request,
                "pages/start_new_plan.html",
                {
                    "meta_title": "Start New Plan",
                    "active_page": "start_new_plan",
                    "topbar_context": "Start New Plan",
                    "groups": user_groups,
                    "error": "Per favor, selecciona un grup per proposar el pla.",
                },
            )

        group = _resolve_group_for_request(request, group_id)
        if _active_group_proposal(group):
            return render(
                request,
                "pages/start_new_plan.html",
                {
                    "meta_title": "Start New Plan",
                    "active_page": "start_new_plan",
                    "topbar_context": "Start New Plan",
                    "groups": user_groups,
                    "error": "Aquest grup ja te una votacio activa. Tanca-la abans de crear-ne una altra.",
                    "default_voting_end_date": request.POST.get("voting_end_date") or default_voting_end.date().isoformat(),
                    "default_voting_end_time": request.POST.get("voting_end_time") or default_voting_end.strftime("%H:%M"),
                },
            )

        try:
            voting_ends_at = _parse_voting_end(request)
        except ValueError as exc:
            return render(
                request,
                "pages/start_new_plan.html",
                {
                    "meta_title": "Start New Plan",
                    "active_page": "start_new_plan",
                    "topbar_context": "Start New Plan",
                    "groups": user_groups,
                    "error": str(exc),
                    "default_voting_end_date": request.POST.get("voting_end_date") or default_voting_end.date().isoformat(),
                    "default_voting_end_time": request.POST.get("voting_end_time") or default_voting_end.strftime("%H:%M"),
                },
            )

        proposal = PlanProposal.objects.create(
            group=group,
            created_by=created_by,
            title=global_title,
            description=global_description,
            voting_ends_at=voting_ends_at,
            status=PlanProposal.Status.VOTING,
        )
        group.status = Group.Status.VOTING
        group.save(update_fields=["status"])

        if not options:
            Plan.objects.create(
                proposal=proposal,
                group=group,
                created_by=created_by,
                title=global_title,
                description=global_description,
                price=request.POST.get("price") or 0,
                status=Plan.Status.PROPOSED,
                option_order=1,
            )
        else:
            for idx, opt in enumerate(options, start=1):
                Plan.objects.create(
                    proposal=proposal,
                    group=group,
                    created_by=created_by,
                    title=opt.get("title") or global_title,
                    description=global_description,
                    price=opt.get("price") or 0,
                    scheduled_for=opt.get("scheduled_for"),
                    place_name=opt.get("place_name", ""),
                    address=opt.get("address", ""),
                    tag=opt.get("tag", ""),
                    status=Plan.Status.PROPOSED,
                    option_order=idx,
                )

        return redirect("dashboard")

    return render(
        request,
        "pages/start_new_plan.html",
        {
            "meta_title": "Start New Plan",
            "active_page": "start_new_plan",
            "topbar_context": "Start New Plan",
            "groups": user_groups,
            "default_voting_end_date": default_voting_end.date().isoformat(),
            "default_voting_end_time": default_voting_end.strftime("%H:%M"),
        },
    )


def vote(request, group_id):
    group = _resolve_group_for_request(request, group_id)
    active_proposal = _decorate_proposal_for_user(_active_group_proposal(group), request.user)
    active_plans = active_proposal.options if active_proposal else Plan.objects.none()
    if request.user.is_authenticated:
        current_voter = _resolve_member(group, request.user).display_name
    else:
        current_voter = "Guest session"

    return render(
        request,
        "pages/vote.html",
        {
            "meta_title": "Vote",
            "active_page": "active_plans",
            "topbar_context": f"Voting - {group.name}",
            "group": group,
            "proposal": active_proposal,
            "plans": active_plans,
            "plan_total": len(active_plans),
            "current_voter": current_voter,
        },
    )


@csrf_exempt
def api_submit_vote(request, plan_id):
    if request.method == "POST":
        plan = get_object_or_404(Plan, id=plan_id)
        try:
            data = json.loads(request.body)
            value = Vote.Value.UP if int(data.get("value", 1)) > 0 else Vote.Value.DOWN
            if plan.proposal.status != PlanProposal.Status.VOTING:
                return JsonResponse({"status": "error", "message": "This voting round is closed."}, status=400)
            identity = _vote_identity_for_request(request, plan)

            Vote.objects.update_or_create(
                plan=plan,
                user=identity["user"],
                member=identity["member"],
                session_key=identity["session_key"],
                defaults={"value": value},
            )
            return JsonResponse({"status": "success"})
        except PermissionDenied as exc:
            return JsonResponse({"status": "error", "message": str(exc)}, status=403)
        except Exception as exc:
            return JsonResponse({"status": "error", "message": str(exc)}, status=400)
    return JsonResponse({"status": "method_not_allowed"}, status=405)
