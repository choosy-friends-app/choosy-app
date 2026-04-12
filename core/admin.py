from django.contrib import admin
from django.db.models import Count, Q

from .models import Group, GroupMember, Plan, Vote


class GroupMemberInline(admin.TabularInline):
    model = GroupMember
    extra = 0
    fields = ("display_name", "user", "role", "status", "avatar_url")


class PlanInline(admin.TabularInline):
    model = Plan
    extra = 0
    fields = ("title", "status", "price", "tag")
    show_change_link = True


@admin.register(Group)
class GroupAdmin(admin.ModelAdmin):
    list_display = ("name", "status", "owner", "member_count", "plan_count", "created_at")
    list_filter = ("status",)
    search_fields = ("name", "description")
    inlines = [GroupMemberInline, PlanInline]

    def get_queryset(self, request):
        return super().get_queryset(request).annotate(_member_count=Count("members"), _plan_count=Count("plans"))

    @admin.display(ordering="_member_count")
    def member_count(self, obj):
        return obj._member_count

    @admin.display(ordering="_plan_count")
    def plan_count(self, obj):
        return obj._plan_count


@admin.register(Plan)
class PlanAdmin(admin.ModelAdmin):
    list_display = ("title", "group", "status", "price", "vote_score", "vote_count", "created_at")
    list_filter = ("status", "group")
    search_fields = ("title", "description", "place_name", "address")

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.annotate(
            _vote_count=Count("votes"),
            _vote_score=Count("votes", filter=Q(votes__value=Vote.Value.UP)),
        )

    @admin.display(ordering="_vote_count")
    def vote_count(self, obj):
        return obj._vote_count

    @admin.display(ordering="_vote_score")
    def vote_score(self, obj):
        return obj._vote_score


@admin.register(GroupMember)
class GroupMemberAdmin(admin.ModelAdmin):
    list_display = ("display_name", "group", "user", "role", "status", "created_at")
    list_filter = ("role", "status", "group")
    search_fields = ("display_name", "group__name", "user__username")


@admin.register(Vote)
class VoteAdmin(admin.ModelAdmin):
    list_display = ("plan", "value", "member", "user", "session_key", "created_at")
    list_filter = ("value", "plan__group")
    search_fields = ("plan__title", "session_key", "user__username", "member__display_name")
