from django.urls import path

from . import views

urlpatterns = [
    path("login/", views.login_view, name="login"),
    path("register/", views.register_view, name="register"),
    path("logout/", views.logout_view, name="logout"),
    path("", views.dashboard, name="dashboard"),
    path("active-plans/", views.active_plans, name="active_plans"),
    path("archive/", views.archive, name="archive"),
    path("start-new-plan/", views.start_new_plan, name="start_new_plan"),
    path("groups/", views.groups, name="groups"),
    path("vote/<int:group_id>/", views.vote, name="vote"),
    path("api/groups/", views.api_create_group, name="api_create_group"),
    path("api/groups/<int:group_id>/members/", views.api_add_group_member, name="api_add_group_member"),
    path("api/vote/<int:plan_id>/", views.api_submit_vote, name="api_submit_vote"),
    
    path("notifications/", views.notification_center, name="notifications"),
    path("invitation/<int:group_id>/", views.invitation_detail, name="invitation_detail"),
    path("css/dashboard_styles.css", views.dashboard_css, name="dashboard_css"),
    path("api/groups/<int:group_id>/invite/", views.api_invite_user, name="api_invite_user"),
    path("api/groups/<int:group_id>/invitation/<str:action>/", views.api_respond_invitation, name="api_respond_invitation"),
]
