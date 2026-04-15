import json

from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.csrf import csrf_exempt

from core.models import Group, GroupMember, Notification, PlanProposal
from core.web.shared import (
    User,
    _active_group_proposal,
    _create_notification,
    _decorate_group_interests,
    _decorate_notification,
    _require_group_admin,
)


def notification_center(request):
    if not request.user.is_authenticated:
        return redirect("login")

    notifications = [
        _decorate_notification(notification)
        for notification in Notification.objects.filter(recipient=request.user).select_related(
            "group", "plan_proposal", "sender"
        )
    ]
    unread_count = sum(1 for notification in notifications if not notification.is_read)
    invitation_count = sum(1 for notification in notifications if notification.type == Notification.Type.INVITATION)
    decision_count = sum(1 for notification in notifications if notification.type == Notification.Type.DECISION)
    related_group_ids = {notification.group_id for notification in notifications if notification.group_id}

    return render(
        request,
        "pages/notifications.html",
        {
            "meta_title": "Notifications",
            "active_page": "notifications",
            "topbar_context": "Notifications",
            "notifications": notifications,
            "unread_count": unread_count,
            "invitation_count": invitation_count,
            "decision_count": decision_count,
            "related_group_count": len(related_group_ids),
        },
    )


def invitation_detail(request, group_id):
    if not request.user.is_authenticated:
        return redirect("login")

    group = get_object_or_404(Group, id=group_id)
    
    # Check if for some reason the user is already an active member
    existing_member = GroupMember.objects.filter(group=group, user=request.user).first()
    
    if existing_member and existing_member.status == GroupMember.Status.ACTIVE:
        # Already in, no need to invite
        return redirect("dashboard") # Or to a specific group page if it exists
    
    # If they are invited, get that record
    member = GroupMember.objects.filter(
        group=group,
        user=request.user,
        status=GroupMember.Status.INVITED,
    ).first()

    # Fallback for God-Mode preview or if they just stumbled upon the link
    if not member:
        # If no invite exists, we might want to allow them to "Request to join" 
        # but for now, let's just make it not 404 if group exists.
        # We can pass a 'mock' member for preview if needed, or a 'guest' state.
        pass

    active_plan = _active_group_proposal(group)
    active_members = list(group.members.filter(status=GroupMember.Status.ACTIVE).select_related("user")[:4])
    active_member_count = group.members.filter(status=GroupMember.Status.ACTIVE).count()
    pending_invites_count = group.members.filter(status=GroupMember.Status.INVITED).count()
    invitation_interests = _decorate_group_interests(group.interests, include_defaults=True)
    invitation_description = (
        group.mission_statement
        or group.description
        or "A collective of friends ready to choose the next plan together."
    )
    active_plan_description = ""
    if active_plan is not None:
        active_plan_description = (
            active_plan.description
            or "There is already a live group vote waiting for your answer once you join."
        )

    return render(
        request,
        "pages/invitation_detail.html",
        {
            "meta_title": f"Invitation: {group.name}",
            "group": group,
            "member": member,
            "active_plan": active_plan,
            "preview_members": active_members,
            "active_member_count": active_member_count,
            "extra_member_count": max(active_member_count - len(active_members), 0),
            "pending_invites_count": pending_invites_count,
            "invitation_interests": invitation_interests,
            "invitation_description": invitation_description,
            "active_plan_description": active_plan_description,
        },
    )


@csrf_exempt
def api_invite_user(request, group_id):
    if request.method != "POST":
        return JsonResponse({"error": "Method not allowed"}, status=405)
    if not request.user.is_authenticated:
        return JsonResponse({"error": "Unauthorized"}, status=401)

    group = get_object_or_404(Group, id=group_id)
    _require_group_admin(group, request.user)

    try:
        data = json.loads(request.body)
        username = data.get("username", "").strip()

        target_user = User.objects.filter(username=username).first()
        if not target_user:
            return JsonResponse({"error": "User not found"}, status=404)

        member, created = GroupMember.objects.get_or_create(
            group=group,
            user=target_user,
            defaults={
                "display_name": target_user.get_full_name() or target_user.username,
                "role": GroupMember.Role.MEMBER,
                "status": GroupMember.Status.INVITED,
                "invited_by": request.user,
            },
        )

        if not created and member.status != GroupMember.Status.LEFT:
            return JsonResponse({"error": "User is already in the group or invited"}, status=400)

        member.status = GroupMember.Status.INVITED
        member.save()

        _create_notification(
            recipient=target_user,
            sender=request.user,
            type=Notification.Type.INVITATION,
            title=f"Invitation to {group.name}",
            message=f"{request.user.username} invited you to '{group.name}'",
            group=group,
        )
        return JsonResponse({"status": "ok"})
    except Exception as exc:
        return JsonResponse({"error": str(exc)}, status=400)


@csrf_exempt
def api_respond_invitation(request, group_id, action):
    if request.method != "POST":
        return JsonResponse({"error": "Method not allowed"}, status=405)
    if not request.user.is_authenticated:
        return JsonResponse({"error": "Unauthorized"}, status=401)

    group = get_object_or_404(Group, id=group_id)
    member = get_object_or_404(GroupMember, group=group, user=request.user, status=GroupMember.Status.INVITED)

    if action == "accept":
        member.status = GroupMember.Status.ACTIVE
        member.save()

        Notification.objects.filter(
            recipient=request.user,
            group=group,
            type=Notification.Type.INVITATION,
        ).update(
            is_read=True, 
            title=f"Joined {group.name}", 
            message=f"You are now a member of '{group.name}'."
        )

        active_proposal = _active_group_proposal(group)
        if active_proposal is not None:
            Notification.objects.get_or_create(
                recipient=request.user,
                type=Notification.Type.NEW_PLAN,
                group=group,
                plan_proposal=active_proposal,
                defaults={
                    "sender": active_proposal.created_by,
                    "title": f"New voting round in {group.name}",
                    "message": f"You joined {group.name} and can now vote on '{active_proposal.title}'.",
                },
            )

        return JsonResponse({"status": "accepted", "group_name": group.name})

    if action == "decline":
        member.status = GroupMember.Status.LEFT
        member.save()

        Notification.objects.filter(
            recipient=request.user,
            group=group,
            type=Notification.Type.INVITATION,
        ).update(is_read=True)

        return JsonResponse({"status": "declined"})

    return JsonResponse({"error": "Invalid action"}, status=400)


@csrf_exempt
def api_mark_notifications_read(request):
    if request.method != "POST":
        return JsonResponse({"error": "Method not allowed"}, status=405)
    if not request.user.is_authenticated:
        return JsonResponse({"error": "Unauthorized"}, status=401)

    updated_count = Notification.objects.filter(recipient=request.user, is_read=False).update(is_read=True)
    return JsonResponse({"status": "ok", "updated_count": updated_count})


def api_notification_status(request):
    if not request.user.is_authenticated:
        return JsonResponse({"status": "ok", "unread_count": 0, "latest": None})

    latest_notification = (
        Notification.objects.filter(recipient=request.user, is_read=False)
        .select_related("group")
        .order_by("-created_at")
        .first()
    )

    latest_payload = None
    if latest_notification is not None:
        latest_payload = {
            "id": latest_notification.id,
            "title": latest_notification.title,
            "message": latest_notification.message,
            "group_name": latest_notification.group.name if latest_notification.group else "",
        }

    return JsonResponse(
        {
            "status": "ok",
            "unread_count": Notification.objects.filter(recipient=request.user, is_read=False).count(),
            "latest": latest_payload,
        }
    )
