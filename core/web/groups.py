import json

from django.core.exceptions import PermissionDenied
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render
from django.views.decorators.csrf import csrf_exempt

from core.models import Group, GroupMember, Notification
from core.web.shared import (
    User,
    _create_notification,
    _decorate_groups,
    _leave_group,
    _remove_group_member,
    _require_group_admin,
    _resolve_group_for_request,
    _seed_demo_groups,
    _set_group_member_role,
    _user_groups_queryset,
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
                    mission_statement = (request.POST.get("mission_statement") or "").strip()
                    hero_image_url = (request.POST.get("hero_image_url") or "").strip()
                    
                    if not name:
                        raise ValueError("El nombre del grupo es obligatorio.")
                    group = Group.objects.create(
                        name=name,
                        description=description,
                        mission_statement=mission_statement,
                        hero_image_url=hero_image_url,
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
                    target_user = get_object_or_404(User, username=username)

                    member, created = GroupMember.objects.get_or_create(
                        group=group,
                        user=target_user,
                        defaults={
                            "display_name": request.POST.get("display_name", "")
                            or target_user.get_full_name()
                            or target_user.username,
                            "role": GroupMember.Role.MEMBER,
                            "status": GroupMember.Status.INVITED,
                            "invited_by": request.user,
                        },
                    )

                    if not created and member.status != GroupMember.Status.LEFT:
                        error_message = "User is already in the group or invited."
                    else:
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
                        success_message = f"Invitación enviada a {member.display_name}."
                elif action == "leave_group":
                    group = _resolve_group_for_request(request, request.POST.get("group_id"))
                    previous_owner_id = group.owner_id
                    _leave_group(group, request.user)
                    if previous_owner_id == request.user.id and group.owner_id:
                        promoted_member = group.members.filter(user_id=group.owner_id).first()
                        promoted_name = promoted_member.display_name if promoted_member else "another member"
                        success_message = f"Has salido de '{group.name}'. {promoted_name} ahora es el owner del grupo."
                    elif previous_owner_id == request.user.id:
                        success_message = (
                            f"Has salido de '{group.name}'. "
                            "El grupo se ha quedado sin owner porque no quedaban miembros activos."
                        )
                    else:
                        success_message = f"Has salido de '{group.name}'."
                elif action == "remove_member":
                    group = _resolve_group_for_request(request, request.POST.get("group_id"))
                    removed_member = _remove_group_member(group, request.user, request.POST.get("member_id"))
                    success_message = f"{removed_member.display_name} ya no forma parte de '{group.name}'."
                elif action == "promote_admin":
                    group = _resolve_group_for_request(request, request.POST.get("group_id"))
                    promoted_member = _set_group_member_role(
                        group,
                        request.user,
                        request.POST.get("member_id"),
                        GroupMember.Role.ADMIN,
                    )
                    success_message = f"{promoted_member.display_name} ahora es admin en '{group.name}'."
                elif action == "demote_admin":
                    group = _resolve_group_for_request(request, request.POST.get("group_id"))
                    demoted_member = _set_group_member_role(
                        group,
                        request.user,
                        request.POST.get("member_id"),
                        GroupMember.Role.MEMBER,
                    )
                    success_message = f"{demoted_member.display_name} vuelve a ser member en '{group.name}'."
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
        mission_statement = (data.get("mission_statement") or "").strip()
        hero_image_url = (data.get("hero_image_url") or "").strip()
        
        if not name:
            return JsonResponse({"status": "error", "message": "Group name is required."}, status=400)

        group = Group.objects.create(
            name=name,
            description=description,
            mission_statement=mission_statement,
            hero_image_url=hero_image_url,
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
