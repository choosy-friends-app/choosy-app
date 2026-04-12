import json

from django.contrib.auth import get_user_model
from django.contrib.auth import authenticate, login, logout
from django.core.exceptions import PermissionDenied
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.csrf import csrf_exempt

from .models import Group, GroupMember, Plan, Vote

User = get_user_model()


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


def _decorate_groups(groups):
    decorated = []
    for group in groups:
        members = list(group.members.filter(status=GroupMember.Status.ACTIVE)[:4])
        group.member_count = group.members.filter(status=GroupMember.Status.ACTIVE).count()
        group.voting_plans_count = Plan.objects.filter(group=group, status=Plan.Status.VOTING).count()
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


def dashboard(request):
    user_groups = _user_groups_queryset(request)

    if not request.user.is_authenticated and not user_groups.exists():
        _seed_demo_groups()
        user_groups = _user_groups_queryset(request)

    user_groups = _decorate_groups(user_groups)
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
    return render(
        request,
        "pages/active_plans.html",
        {
            "meta_title": "Active Plans",
            "active_page": "active_plans",
            "topbar_context": "Active Plans",
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

    user_groups = _decorate_groups(user_groups)
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

        if not options:
            Plan.objects.create(
                group=group,
                created_by=created_by,
                title=global_title,
                description=global_description,
                price=request.POST.get("price") or 0,
                status=Plan.Status.VOTING,
            )
        else:
            for opt in options:
                Plan.objects.create(
                    group=group,
                    created_by=created_by,
                    title=opt.get("title") or global_title,
                    description=global_description,
                    price=opt.get("price") or 0,
                    scheduled_for=opt.get("scheduled_for"),
                    place_name=opt.get("place_name", ""),
                    address=opt.get("address", ""),
                    tag=opt.get("tag", ""),
                    status=Plan.Status.VOTING,
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
        },
    )


def vote(request, group_id):
    group = _resolve_group_for_request(request, group_id)
    active_plans = Plan.objects.filter(group=group, status=Plan.Status.VOTING)
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
            "plans": active_plans,
            "current_voter": current_voter,
        },
    )


@csrf_exempt
def api_submit_vote(request, plan_id):
    if request.method == "POST":
        plan = get_object_or_404(Plan, id=plan_id)
        try:
            data = json.loads(request.body)
            value = data.get("value", 1)
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
