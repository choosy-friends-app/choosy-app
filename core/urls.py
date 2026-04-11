from django.urls import path

from . import views

urlpatterns = [
    path("", views.dashboard, name="dashboard"),
    path("active-plans/", views.active_plans, name="active_plans"),
    path("archive/", views.archive, name="archive"),
    path("start-new-plan/", views.start_new_plan, name="start_new_plan"),
    path("groups/", views.groups, name="groups"),
    path("vote/<int:group_id>/", views.vote, name="vote"),
    path("api/vote/<int:plan_id>/", views.api_submit_vote, name="api_submit_vote"),
]
