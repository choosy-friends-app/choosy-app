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
    path("crear-grupo/", views.GroupCreateView.as_view(), name="crear_grupo"),
    path("editar-grupo/<int:pk>/", views.GroupUpdateView.as_view(), name="editar_grupo"),
    path("eliminar-grupo/<int:pk>/", views.GroupDeleteView.as_view(), name="eliminar_grupo"),
    path("crear-propuesta/", views.PlanProposalCreateView.as_view(), name="crear_propuesta"),
    path("editar-propuesta/<int:pk>/", views.PlanProposalUpdateView.as_view(), name="editar_propuesta"),
    path("eliminar-propuesta/<int:pk>/", views.PlanProposalDeleteView.as_view(), name="eliminar_propuesta"),
    path("crear-plan/", views.PlanCreateView.as_view(), name="crear_plan"),
    path("editar-plan/<int:pk>/", views.PlanUpdateView.as_view(), name="editar_plan"),
    path("eliminar-plan/<int:pk>/", views.PlanDeleteView.as_view(), name="eliminar_plan"),
    path("vote/<int:group_id>/", views.vote, name="vote"),
    path("api/groups/", views.api_create_group, name="api_create_group"),
    path("api/groups/<int:group_id>/members/", views.api_add_group_member, name="api_add_group_member"),
    path("api/vote/<int:plan_id>/", views.api_submit_vote, name="api_submit_vote"),
    path("api/locations/search/", views.api_location_search, name="api_location_search"),
    path("api/weather/forecast/", views.api_weather_forecast, name="api_weather_forecast"),
    
    path("notifications/", views.notification_center, name="notifications"),
    path("invitation/<int:group_id>/", views.invitation_detail, name="invitation_detail"),
    path("css/dashboard_styles.css", views.dashboard_css, name="dashboard_css"),
    path("api/groups/<int:group_id>/invite/", views.api_invite_user, name="api_invite_user"),
    path("api/groups/<int:group_id>/invitation/<str:action>/", views.api_respond_invitation, name="api_respond_invitation"),
    path("api/notifications/read-all/", views.api_mark_notifications_read, name="api_mark_notifications_read"),
    path("api/notifications/clear/", views.api_clear_notifications, name="api_clear_notifications"),
    path("api/notifications/status/", views.api_notification_status, name="api_notification_status"),
]
