from django.contrib import admin
from django.urls import path

from core import views

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", views.home, name="home"),
    path("groups/", views.groups, name="groups"),
    path("discover/", views.discover, name="discover"),
    path("profile/", views.profile, name="profile"),
    path("vote/", views.vote_plan, name="vote"),
]
