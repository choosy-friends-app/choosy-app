from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q
from django.utils import timezone


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

    def add_member(
        self,
        *,
        user=None,
        display_name: str = "",
        avatar_url: str = "",
        role: str = "member",
        invited_by=None,
    ):
        if not display_name and user is not None:
            display_name = user.get_full_name() or user.get_username()

        member, _ = GroupMember.objects.update_or_create(
            group=self,
            user=user,
            defaults={
                "display_name": display_name[:80] or "Member",
                "avatar_url": avatar_url,
                "role": role,
                "status": GroupMember.Status.ACTIVE,
                "invited_by": invited_by,
            },
        )
        return member


class GroupMember(TimestampedModel):
    class Role(models.TextChoices):
        OWNER = "owner", "Owner"
        ADMIN = "admin", "Admin"
        MEMBER = "member", "Member"

    class Status(models.TextChoices):
        INVITED = "invited", "Invited"
        ACTIVE = "active", "Active"
        LEFT = "left", "Left"

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
    role = models.CharField(max_length=16, choices=Role.choices, default=Role.MEMBER)
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.ACTIVE)
    invited_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="sent_group_invites",
    )

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

    @property
    def is_admin(self) -> bool:
        return self.role in {self.Role.OWNER, self.Role.ADMIN}

    def clean(self) -> None:
        if not self.display_name and self.user is not None:
            self.display_name = self.user.get_full_name() or self.user.get_username()

        if self.role == self.Role.OWNER and self.user is None:
            raise ValidationError("Owner membership requires a linked user.")


class PlanProposal(TimestampedModel):
    class Status(models.TextChoices):
        DRAFT = "draft", "Draft"
        VOTING = "voting", "Voting"
        CHOSEN = "chosen", "Chosen"
        CANCELLED = "cancelled", "Cancelled"

    group = models.ForeignKey(Group, on_delete=models.CASCADE, related_name="proposals")
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="created_plan_proposals",
    )
    title = models.CharField(max_length=120)
    description = models.CharField(max_length=255, blank=True)
    voting_ends_at = models.DateTimeField(null=True, blank=True)
    chosen_plan = models.ForeignKey(
        "Plan",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="chosen_for_proposals",
    )
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.VOTING)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["group", "status"]),
            models.Index(fields=["status", "created_at"]),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=["group"],
                condition=Q(status__in=["draft", "voting"]),
                name="unique_open_proposal_per_group",
            )
        ]

    def __str__(self) -> str:
        return self.title

    @property
    def is_open(self) -> bool:
        return self.status in {self.Status.DRAFT, self.Status.VOTING}

    @property
    def is_expired(self) -> bool:
        return bool(self.voting_ends_at and self.voting_ends_at <= timezone.now())

    @property
    def can_accept_votes(self) -> bool:
        return self.status == self.Status.VOTING and not self.is_expired

    def clean(self) -> None:
        if self.chosen_plan and self.chosen_plan.proposal_id != self.id:
            raise ValidationError("Chosen plan must belong to this proposal.")


class Plan(TimestampedModel):
    class Status(models.TextChoices):
        PROPOSED = "proposed", "Proposed"
        SHORTLISTED = "shortlisted", "Shortlisted"
        CHOSEN = "chosen", "Chosen"
        ARCHIVED = "archived", "Archived"

    proposal = models.ForeignKey(PlanProposal, on_delete=models.CASCADE, related_name="plans")
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
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PROPOSED)
    scheduled_for = models.DateTimeField(null=True, blank=True)
    option_order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["proposal", "option_order"]),
            models.Index(fields=["group", "status"]),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=["proposal", "option_order"],
                name="unique_plan_option_order_per_proposal",
            )
        ]

    def __str__(self) -> str:
        return self.title

    def clean(self) -> None:
        if self.proposal and self.group_id != self.proposal.group_id:
            raise ValidationError("Plan option must belong to the same group as its proposal.")


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
        if self.member and self.member.group_id != self.plan.group_id:
            raise ValidationError("Vote member must belong to the same group as the plan.")
        if self.user and self.member and self.member.user_id != self.user_id:
            raise ValidationError("Vote user and member must refer to the same identity.")

    def __str__(self) -> str:
        return f"Vote(plan={self.plan_id}, value={self.value})"


class Notification(TimestampedModel):
    class Type(models.TextChoices):
        INVITATION = "invitation", "Invitation"
        NEW_PLAN = "new_plan", "New Plan"
        DECISION = "decision", "Decision"
        REMINDER = "reminder", "Reminder"

    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="notifications"
    )
    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="sent_notifications"
    )
    type = models.CharField(max_length=20, choices=Type.choices)
    title = models.CharField(max_length=120)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    
    # Context references
    group = models.ForeignKey(
        Group,
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name="notifications"
    )
    plan_proposal = models.ForeignKey(
        PlanProposal,
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name="notifications"
    )

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["recipient", "is_read", "-created_at"]),
        ]

    def __str__(self) -> str:
        return f"{self.type}: {self.title} for {self.recipient.username}"
