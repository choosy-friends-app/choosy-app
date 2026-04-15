from core.web.shared import _attention_notifications_for_user


def notification_status(request):
    if not request.user.is_authenticated:
        return {
            "topbar_unread_count": 0,
            "topbar_latest_notification": None,
        }

    attention_notifications = _attention_notifications_for_user(request.user)
    latest_notification = attention_notifications[0] if attention_notifications else None

    return {
        "topbar_unread_count": len(attention_notifications),
        "topbar_latest_notification": latest_notification,
    }
