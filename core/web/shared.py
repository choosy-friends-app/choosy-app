from datetime import datetime, timedelta

from django.contrib.auth import get_user_model
from django.core.exceptions import PermissionDenied
from django.db.models import Q
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.utils import timezone

from core.models import Group, GroupMember, Notification, Plan, PlanProposal, Vote

User = get_user_model()


INTEREST_ICON_KEYWORDS = (
    (("food", "culinary", "taste", "restaurant", "dinner", "lunch", "brunch", "pizza"), "restaurant"),
    (("night", "club", "party", "drink", "bar", "cocktail"), "nightlife"),
    (("adventure", "explorer", "nature", "hike", "outdoor", "mountain"), "explore"),
    (("sport", "active", "football", "soccer", "run", "gym", "padel"), "sports_soccer"),
    (("art", "culture", "museum", "gallery", "cinema", "music"), "palette"),
)

GROUP_ACTIVITY_OPTIONS = (
    {
        "label": "Food",
        "icon": "restaurant",
        "image_url": "https://images.unsplash.com/photo-1555396273-367ea4eb4db5?q=80&w=900&auto=format&fit=crop",
        "selected": True,
    },
    {
        "label": "Nightlife",
        "icon": "nightlife",
        "image_url": "https://images.unsplash.com/photo-1514525253161-7a46d19cd819?q=80&w=900&auto=format&fit=crop",
        "selected": True,
    },
    {
        "label": "Adventure",
        "icon": "explore",
        "image_url": "https://images.unsplash.com/photo-1500530855697-b586d89ba3ee?q=80&w=900&auto=format&fit=crop",
        "selected": True,
    },
    {
        "label": "Sport",
        "icon": "sports_soccer",
        "image_url": "https://images.unsplash.com/photo-1461896836934-ffe607ba8211?q=80&w=900&auto=format&fit=crop",
        "selected": True,
    },
    {
        "label": "Culture",
        "icon": "palette",
        "image_url": "https://images.unsplash.com/photo-1564399580075-5dfe19c205f3?q=80&w=900&auto=format&fit=crop",
        "selected": False,
    },
    {
        "label": "Travel",
        "icon": "flight_takeoff",
        "image_url": "https://images.unsplash.com/photo-1507525428034-b723cf961d3e?q=80&w=900&auto=format&fit=crop",
        "selected": False,
    },
)

DEFAULT_GROUP_INTERESTS = (
    {"label": "Shared Plans", "icon": "auto_awesome"},
    {"label": "Curated Picks", "icon": "verified"},
)


def _interest_icon(interest):
    normalized_interest = str(interest or "").lower()
    if normalized_interest == "travel":
        return "flight_takeoff"
    for keywords, icon in INTEREST_ICON_KEYWORDS:
        if any(keyword in normalized_interest for keyword in keywords):
            return icon
    return "choosy"


def _parse_group_interests(raw_interests):
    if isinstance(raw_interests, str):
        items = raw_interests.split(",")
    elif raw_interests:
        items = raw_interests
    else:
        items = []

    interests = []
    seen = set()
    for item in items:
        label = str(item or "").strip()
        key = label.lower()
        if not label or key in seen:
            continue
        interests.append(label[:48])
        seen.add(key)
    return interests[:8]


def _decorate_group_interests(interests, *, include_defaults=False):
    decorated = [
        {
            "label": label,
            "icon": _interest_icon(label),
        }
        for label in _parse_group_interests(interests)
    ]
    if decorated or not include_defaults:
        return decorated
    return list(DEFAULT_GROUP_INTERESTS)


def _default_voting_end():
    return timezone.now() + timedelta(hours=24)


def _create_notification(*, recipient, type, title, message, sender=None, group=None, plan_proposal=None):
    return Notification.objects.create(
        recipient=recipient,
        sender=sender,
        type=type,
        title=title,
        message=message,
        group=group,
        plan_proposal=plan_proposal,
    )


def _notify_group_members_about_new_plan(group, proposal, sender=None):
    recipients = (
        group.members.filter(status=GroupMember.Status.ACTIVE, user__isnull=False)
        .exclude(user=sender)
        .select_related("user")
    )
    actor_name = sender.username if sender else "Someone"

    for member in recipients:
        Notification.objects.get_or_create(
            recipient=member.user,
            type=Notification.Type.NEW_PLAN,
            group=group,
            plan_proposal=proposal,
            defaults={
                "sender": sender,
                "title": f"New voting round in {group.name}",
                "message": f"{actor_name} started '{proposal.title}' and your vote is now needed.",
            },
        )


def _notify_group_members_about_decision(proposal):
    chosen_plan = proposal.chosen_plan
    if chosen_plan is None:
        return

    recipients = proposal.group.members.filter(
        status=GroupMember.Status.ACTIVE,
        user__isnull=False,
    ).select_related("user")
    for member in recipients:
        Notification.objects.get_or_create(
            recipient=member.user,
            type=Notification.Type.DECISION,
            group=proposal.group,
            plan_proposal=proposal,
            defaults={
                "title": f"Decision made in {proposal.group.name}",
                "message": f"'{chosen_plan.title}' won the vote for '{proposal.title}'.",
            },
        )


def _decorate_notification(notification):
    notification.cta_url = ""
    notification.cta_label = ""
    notification.is_joined_invitation = False
    notification.is_declined_invitation = False
    notification.is_resolved_plan_notification = False

    if notification.type == Notification.Type.INVITATION and notification.group_id:
        invited_member = notification.group.members.filter(
            user=notification.recipient,
            status=GroupMember.Status.INVITED,
        ).exists()
        active_member = notification.group.members.filter(
            user=notification.recipient,
            status=GroupMember.Status.ACTIVE,
        ).exists()
        left_member = notification.group.members.filter(
            user=notification.recipient,
            status=GroupMember.Status.LEFT,
        ).exists()
        notification.is_joined_invitation = active_member
        notification.is_declined_invitation = left_member
        if active_member:
            notification.cta_url = reverse("groups")
            notification.cta_label = "View group"
        elif invited_member:
            notification.cta_url = reverse("invitation_detail", args=[notification.group_id])
            notification.cta_label = "View invitation"
        elif left_member:
            notification.cta_url = reverse("notifications")
            notification.cta_label = "Reviewed"
        else:
            notification.cta_url = reverse("groups")
            notification.cta_label = "View groups"
    elif notification.type == Notification.Type.NEW_PLAN and notification.group_id:
        notification.is_resolved_plan_notification = not _new_plan_notification_needs_attention(notification)
        if notification.is_resolved_plan_notification:
            notification.cta_url = reverse("groups")
            notification.cta_label = "Reviewed"
        else:
            notification.cta_url = reverse("vote", args=[notification.group_id])
            notification.cta_label = "Vote now"
    elif notification.type == Notification.Type.DECISION and notification.group_id:
        notification.cta_url = reverse("groups")
        notification.cta_label = "View group"

    notification.is_actionable = bool(notification.cta_url)
    return notification


def _proposal_vote_progress_for_user(proposal, user):
    if proposal is None or user is None or not user.is_authenticated:
        return 0, 0

    option_count = proposal.plans.count()
    if option_count == 0:
        return 0, 0

    member = proposal.group.members.filter(user=user, status=GroupMember.Status.ACTIVE).first()
    if member is None:
        return 0, option_count

    voted_count = (
        Vote.objects.filter(plan__proposal=proposal, member=member)
        .values("plan_id")
        .distinct()
        .count()
    )
    return voted_count, option_count


def _user_completed_proposal_vote(proposal, user):
    voted_count, option_count = _proposal_vote_progress_for_user(proposal, user)
    return option_count > 0 and voted_count >= option_count


def _new_plan_notification_needs_attention(notification):
    proposal = notification.plan_proposal
    if proposal is None or not proposal.can_accept_votes:
        return False
    return not _user_completed_proposal_vote(proposal, notification.recipient)


def _notification_needs_attention(notification):
    if notification.is_read:
        return False

    if notification.type == Notification.Type.INVITATION and notification.group_id:
        return notification.group.members.filter(
            user=notification.recipient,
            status=GroupMember.Status.INVITED,
        ).exists()

    if notification.type == Notification.Type.NEW_PLAN:
        return _new_plan_notification_needs_attention(notification)

    return True


def _sync_user_notification_states(user):
    if user is None or not user.is_authenticated:
        return 0

    notifications = list(
        Notification.objects.filter(recipient=user, is_read=False).select_related(
            "group",
            "plan_proposal",
        )
    )
    resolved_ids = [
        notification.id
        for notification in notifications
        if not _notification_needs_attention(notification)
    ]
    if resolved_ids:
        Notification.objects.filter(id__in=resolved_ids).update(is_read=True)
    return len(resolved_ids)


def _attention_notifications_for_user(user):
    if user is None or not user.is_authenticated:
        return []

    _sync_user_notification_states(user)
    notifications = list(
        Notification.objects.filter(recipient=user, is_read=False)
        .select_related("group", "plan_proposal", "sender")
        .order_by("-created_at")
    )
    return [
        notification
        for notification in notifications
        if _notification_needs_attention(notification)
    ]


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
    return Group.objects.none()


def _seed_demo_groups():
    if Group.objects.exists():
        return
    Group.objects.create(
        name="The Foodies Collective",
        description="Culinary adventures",
        interests=["Culinary", "Brunch", "Hidden restaurants"],
    )
    Group.objects.create(
        name="Adventure Seekers",
        description="Outdoor stuff",
        interests=["Adventure", "Nature", "Active weekends"],
    )


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
    _notify_group_members_about_decision(proposal)
    return _decorate_proposal(proposal)


def _sync_proposal_status(proposal):
    if proposal is None:
        return None
    if (
        proposal.status == PlanProposal.Status.VOTING
        and proposal.voting_ends_at
        and proposal.voting_ends_at <= timezone.now()
    ):
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
        preview_members = list(group.members.filter(status=GroupMember.Status.ACTIVE).select_related("user")[:4])
        roster_members = list(
            group.members.filter(status__in=[GroupMember.Status.ACTIVE, GroupMember.Status.INVITED]).select_related("user")
        )
        roster_members.sort(
            key=lambda member: (
                0 if member.role == GroupMember.Role.OWNER else 1 if member.role == GroupMember.Role.ADMIN else 2,
                0 if member.status == GroupMember.Status.ACTIVE else 1,
                member.created_at,
                member.id,
            )
        )
        active_proposal = _decorate_proposal_for_user(
            _sync_proposal_status(
                group.proposals.filter(status=PlanProposal.Status.VOTING).order_by("-created_at").first()
            ),
            user,
        )
        current_member = None
        if user and user.is_authenticated:
            current_member = group.members.filter(user=user, status=GroupMember.Status.ACTIVE).first()
        group.member_count = group.members.filter(status=GroupMember.Status.ACTIVE).count()
        group.active_proposal = active_proposal
        group.voting_plans_count = active_proposal.option_count if active_proposal else 0
        group.activity_chips = _decorate_group_interests(group.interests)
        group.activity_preview = group.activity_chips[:4]
        group.activity_overflow_count = max(len(group.activity_chips) - len(group.activity_preview), 0)
        group.preview_members = preview_members
        group.extra_members_count = max(group.member_count - len(preview_members), 0)
        group.pending_invites_count = group.members.filter(status=GroupMember.Status.INVITED).count()
        group.current_user_is_owner = bool(user and user.is_authenticated and group.owner_id == user.id)
        group.current_user_can_manage = bool(current_member and current_member.is_admin)

        for member in roster_members:
            member.avatar_label = (member.display_name or "M")[:1].upper()
            member.is_owner = member.role == GroupMember.Role.OWNER
            member.is_admin_role = member.role in {GroupMember.Role.OWNER, GroupMember.Role.ADMIN}
            member.role_label = (
                "Owner"
                if member.role == GroupMember.Role.OWNER
                else "Admin" if member.role == GroupMember.Role.ADMIN else "Member"
            )
            member.status_label = "Invited" if member.status == GroupMember.Status.INVITED else "Active"
            member.can_remove = bool(
                group.current_user_can_manage
                and member.role != GroupMember.Role.OWNER
                and (not user or member.user_id != user.id)
                and not (member.role == GroupMember.Role.ADMIN and not group.current_user_is_owner)
            )
            member.can_promote = bool(
                group.current_user_is_owner
                and member.status == GroupMember.Status.ACTIVE
                and member.role == GroupMember.Role.MEMBER
            )
            member.can_demote = bool(
                group.current_user_is_owner
                and member.status == GroupMember.Status.ACTIVE
                and member.role == GroupMember.Role.ADMIN
            )
        group.membership_cards = roster_members
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
        raise PermissionDenied("Authentication required.")
    _resolve_member(group, request.user)
    return group


def _require_group_admin(group, user):
    member = _resolve_member(group, user)
    if not member.is_admin:
        raise PermissionDenied("You do not have permission to manage this group.")
    return member


def _require_group_owner(group, user):
    member = _resolve_member(group, user)
    if group.owner_id != user.id and member.role != GroupMember.Role.OWNER:
        raise PermissionDenied("Only the group owner can change admin roles.")
    return member


def _promote_oldest_active_member(group, departing_member):
    successor = (
        group.members.filter(status=GroupMember.Status.ACTIVE)
        .exclude(id=departing_member.id)
        .exclude(user__isnull=True)
        .order_by("created_at", "id")
        .first()
    )
    if successor is None:
        group.owner = None
        group.save(update_fields=["owner"])
        return None

    successor.role = GroupMember.Role.OWNER
    successor.save(update_fields=["role"])
    group.owner = successor.user
    group.save(update_fields=["owner"])
    return successor


def _leave_group(group, user):
    member = _resolve_member(group, user)
    was_owner = group.owner_id == user.id or member.role == GroupMember.Role.OWNER

    if was_owner:
        _promote_oldest_active_member(group, member)

    member.status = GroupMember.Status.LEFT
    if member.role == GroupMember.Role.OWNER:
        member.role = GroupMember.Role.MEMBER
        member.save(update_fields=["status", "role"])
    else:
        member.save(update_fields=["status"])
    return member


def _set_group_member_role(group, actor, member_id, role):
    _require_group_owner(group, actor)
    target_member = get_object_or_404(
        GroupMember,
        group=group,
        id=member_id,
        status=GroupMember.Status.ACTIVE,
    )
    if target_member.role == GroupMember.Role.OWNER:
        raise PermissionDenied("You cannot change the owner role from this action.")
    if role not in {GroupMember.Role.ADMIN, GroupMember.Role.MEMBER}:
        raise ValueError("Invalid member role.")
    if target_member.role == role:
        return target_member
    target_member.role = role
    target_member.save(update_fields=["role"])
    return target_member


def _remove_group_member(group, actor, member_id):
    _require_group_admin(group, actor)
    target_member = get_object_or_404(
        GroupMember,
        group=group,
        id=member_id,
        status__in=[GroupMember.Status.ACTIVE, GroupMember.Status.INVITED],
    )
    if target_member.user_id == actor.id:
        raise PermissionDenied("Use leave group to remove yourself from the group.")
    if target_member.role == GroupMember.Role.OWNER:
        raise PermissionDenied("The group owner cannot be removed by another admin.")
    if target_member.role == GroupMember.Role.ADMIN and group.owner_id != actor.id:
        raise PermissionDenied("Only the group owner can remove another admin.")

    target_member.status = GroupMember.Status.LEFT
    if target_member.role == GroupMember.Role.ADMIN:
        target_member.role = GroupMember.Role.MEMBER
        target_member.save(update_fields=["status", "role"])
    else:
        target_member.save(update_fields=["status"])

    Notification.objects.filter(
        recipient=target_member.user,
        group=group,
        type=Notification.Type.INVITATION,
        is_read=False,
    ).update(is_read=True)
    return target_member


def _vote_identity_for_request(request, plan):
    if not request.user.is_authenticated:
        raise PermissionDenied("Authentication required.")

    member = _resolve_member(plan.group, request.user)
    return {"user": request.user, "member": member, "session_key": ""}


def _active_group_proposal(group):
    return _sync_proposal_status(
        group.proposals.filter(status=PlanProposal.Status.VOTING).order_by("-created_at").first()
    )
