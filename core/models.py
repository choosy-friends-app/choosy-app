from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q


class TimestampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class Group(TimestampedModel):
    class Status(models.TextChoices):
        PLANNING = "planning", "Planning"
        VOTING = "voting", "Voting"
        ACTIVE = "active", "Active"
        ARCHIVED = "archived", "Archived"

    name = models.CharField(max_length=120)
    description = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PLANNING)
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="owned_groups",
    )

    class Meta:
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["status", "created_at"])]

    def __str__(self) -> str:
        return self.name


class GroupMember(TimestampedModel):
    group = models.ForeignKey(Group, on_delete=models.CASCADE, related_name="members")
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="group_memberships",
    )
    display_name = models.CharField(max_length=80)
    avatar_url = models.URLField(blank=True)
    is_admin = models.BooleanField(default=False)

    class Meta:
        ordering = ["group_id", "id"]
        constraints = [
            models.UniqueConstraint(
                fields=["group", "user"],
                condition=Q(user__isnull=False),
                name="unique_group_user_membership",
            )
        ]

    def __str__(self) -> str:
        return f"{self.display_name} ({self.group.name})"


class Plan(TimestampedModel):
    class Status(models.TextChoices):
        DRAFT = "draft", "Draft"
        VOTING = "voting", "Voting"
        CHOSEN = "chosen", "Chosen"
        CANCELLED = "cancelled", "Cancelled"

    group = models.ForeignKey(Group, on_delete=models.CASCADE, related_name="plans")
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="created_plans",
    )
    title = models.CharField(max_length=120)
    description = models.CharField(max_length=255, blank=True)
    price = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    duration_minutes = models.PositiveIntegerField(null=True, blank=True)
    tag = models.CharField(max_length=40, blank=True)
    image_url = models.URLField(blank=True)
    place_name = models.CharField(max_length=120, blank=True)
    address = models.CharField(max_length=255, blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.VOTING)
    scheduled_for = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["group", "status"]),
            models.Index(fields=["status", "created_at"]),
        ]

    def __str__(self) -> str:
        return self.title


class Vote(TimestampedModel):
    class Value(models.IntegerChoices):
        DOWN = -1, "Downvote"
        UP = 1, "Upvote"

    plan = models.ForeignKey(Plan, on_delete=models.CASCADE, related_name="votes")
    member = models.ForeignKey(
        GroupMember,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="votes",
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="votes",
    )
    session_key = models.CharField(max_length=64, blank=True)
    value = models.SmallIntegerField(choices=Value.choices, default=Value.UP)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["plan", "member"],
                condition=Q(member__isnull=False),
                name="unique_vote_per_member_per_plan",
            ),
            models.UniqueConstraint(
                fields=["plan", "user"],
                condition=Q(user__isnull=False),
                name="unique_vote_per_user_per_plan",
            ),
            models.UniqueConstraint(
                fields=["plan", "session_key"],
                condition=~Q(session_key=""),
                name="unique_vote_per_session_per_plan",
            ),
        ]
        indexes = [models.Index(fields=["plan", "created_at"])]

    def clean(self) -> None:
        if not self.member and not self.user and not self.session_key:
            raise ValidationError("Vote needs member, user or session_key.")

    def __str__(self) -> str:
        return f"Vote(plan={self.plan_id}, value={self.value})"
