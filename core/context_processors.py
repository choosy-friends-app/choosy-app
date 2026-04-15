from core.models import Notification


def notification_status(request):
    if not request.user.is_authenticated:
        return {
            "topbar_unread_count": 0,
            "topbar_latest_notification": None,
        }

    unread_notifications = Notification.objects.filter(
        recipient=request.user,
        is_read=False,
    ).select_related("group")
    latest_notification = unread_notifications.order_by("-created_at").first()

    return {
        "topbar_unread_count": unread_notifications.count(),
        "topbar_latest_notification": latest_notification,
    }
