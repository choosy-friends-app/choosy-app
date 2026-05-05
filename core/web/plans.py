import json

from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render

from core.models import Group, Notification, Plan, PlanProposal, Vote
from core.web.shared import (
    _active_group_proposal,
    _decorate_proposal_for_user,
    _default_voting_end,
    _notify_group_members_about_new_plan,
    _parse_voting_end,
    _resolve_group_for_request,
    _resolve_member,
    _user_completed_proposal_vote,
    _user_groups_queryset,
    _vote_identity_for_request,
)


@login_required
def start_new_plan(request):
    user_groups = _user_groups_queryset(request)
    default_voting_end = _default_voting_end()

    if request.method == "POST":
        group_id = request.POST.get("group_id")
        global_title = request.POST.get("title")
        global_description = request.POST.get("description", "")
        created_by = request.user

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
                    "default_voting_end_date": request.POST.get("voting_end_date")
                    or default_voting_end.date().isoformat(),
                    "default_voting_end_time": request.POST.get("voting_end_time")
                    or default_voting_end.strftime("%H:%M"),
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
                    "default_voting_end_date": request.POST.get("voting_end_date")
                    or default_voting_end.date().isoformat(),
                    "default_voting_end_time": request.POST.get("voting_end_time")
                    or default_voting_end.strftime("%H:%M"),
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

        _notify_group_members_about_new_plan(group, proposal, sender=created_by)
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


@login_required
def vote(request, group_id):
    group = _resolve_group_for_request(request, group_id)
    active_proposal = _decorate_proposal_for_user(_active_group_proposal(group), request.user)
    active_plans = active_proposal.options if active_proposal else Plan.objects.none()
    current_voter = _resolve_member(group, request.user).display_name

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


def api_submit_vote(request, plan_id):
    if request.method != "POST":
        return JsonResponse({"error": "Method not allowed"}, status=405)
    if not request.user.is_authenticated:
        return JsonResponse({"error": "Authentication required"}, status=403)

    try:
        data = json.loads(request.body)
        value = int(data.get("value", 0))
        if value not in {-1, 1}:
            return JsonResponse({"error": "Invalid vote value"}, status=400)

        plan = get_object_or_404(Plan, id=plan_id)
        if not plan.proposal.can_accept_votes:
            return JsonResponse({"error": "Voting is closed"}, status=400)

        ident = _vote_identity_for_request(request, plan)
        Vote.objects.update_or_create(
            plan=plan,
            member=ident["member"],
            user=ident["user"],
            session_key=ident["session_key"],
            defaults={"value": value},
        )
        if request.user.is_authenticated and _user_completed_proposal_vote(plan.proposal, request.user):
            Notification.objects.filter(
                recipient=request.user,
                type=Notification.Type.NEW_PLAN,
                group=plan.group,
                plan_proposal=plan.proposal,
            ).update(is_read=True)
        return JsonResponse({"status": "ok"})
    except PermissionDenied as exc:
        return JsonResponse({"error": str(exc)}, status=403)
    except Exception as exc:
        return JsonResponse({"error": str(exc)}, status=400)
