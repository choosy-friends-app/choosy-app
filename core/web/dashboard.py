from django.http import HttpResponse
from django.shortcuts import render
from django.template.loader import render_to_string

from core.models import Vote
from core.web.shared import (
    _active_group_proposal,
    _decorate_groups,
    _decorate_proposal_for_user,
    _seed_demo_groups,
    _user_groups_queryset,
)


def dashboard(request):
    user_groups = _user_groups_queryset(request)

    if not request.user.is_authenticated and not user_groups.exists():
        _seed_demo_groups()
        user_groups = _user_groups_queryset(request)

    user_groups = _decorate_groups(user_groups, request.user)
    recent_votes = Vote.objects.select_related("plan", "plan__group", "member", "user").order_by("-created_at")[:5]

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


def dashboard_css(request):
    css = render_to_string("includes/dashboard_styles.css")
    return HttpResponse(css, content_type="text/css")
