from django.urls import path

from . import views

urlpatterns = [
    path("", views.dashboard, name="dashboard"),
    path("active-plans/", views.active_plans, name="active_plans"),
    path("start-new-plan/", views.start_new_plan, name="start_new_plan"),
    path("groups/", views.groups, name="groups"),
]
