from core.web.auth import login_view, logout_view, register_view
from core.web.dashboard import active_plans, archive, dashboard, dashboard_css
from core.web.crud import (
    GroupCreateView, GroupUpdateView, GroupDeleteView,
    PlanProposalCreateView, PlanProposalUpdateView, PlanProposalDeleteView,
    PlanCreateView, PlanUpdateView, PlanDeleteView
)
from core.web.groups import api_add_group_member, api_create_group, groups
from core.web.integrations import api_location_search, api_weather_forecast
from core.web.notifications import (
    api_clear_notifications,
    api_invite_user,
    api_mark_notifications_read,
    api_notification_status,
    api_respond_invitation,
    invitation_detail,
    notification_center,
)
from core.web.plans import api_submit_vote, start_new_plan, vote

__all__ = [
    "active_plans",
    "api_add_group_member",
    "api_clear_notifications",
    "api_create_group",
    "api_invite_user",
    "api_location_search",
    "api_mark_notifications_read",
    "api_notification_status",
    "api_respond_invitation",
    "api_submit_vote",
    "api_weather_forecast",
    "archive",
    "dashboard",
    "dashboard_css",
    "groups",
    "GroupCreateView",
    "GroupUpdateView",
    "GroupDeleteView",
    "PlanProposalCreateView",
    "PlanProposalUpdateView",
    "PlanProposalDeleteView",
    "PlanCreateView",
    "PlanUpdateView",
    "PlanDeleteView",
    "invitation_detail",
    "login_view",
    "logout_view",
    "notification_center",
    "register_view",
    "start_new_plan",
    "vote",
]
