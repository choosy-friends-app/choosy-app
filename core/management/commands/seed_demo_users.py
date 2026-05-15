from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

from core.models import Group, GroupMember, PlanProposal


class Command(BaseCommand):
    help = "Create local demo users for testing groups, invites, and voting flows."

    DEFAULT_PASSWORD = "testpass123"
    DEMO_USERS = [
        {
            "username": "aleix",
            "first_name": "Aleix",
            "last_name": "",
            "email": "aleix@example.com",
        },
        {
            "username": "bru",
            "first_name": "Bru",
            "last_name": "",
            "email": "bru@example.com",
        },
        {
            "username": "eldejuneda",
            "first_name": "ElDeJuneda",
            "last_name": "",
            "email": "eldejuneda@example.com",
        },
        {
            "username": "chileno",
            "first_name": "Chileno",
            "last_name": "",
            "email": "chileno@example.com",
        },
    ]

    def handle(self, *args, **options):
        user_model = get_user_model()

        self.stdout.write("Creating demo users for localhost...")
        for user_data in self.DEMO_USERS:
            user, created = user_model.objects.get_or_create(
                username=user_data["username"],
                defaults={
                    "first_name": user_data["first_name"],
                    "last_name": user_data["last_name"],
                    "email": user_data["email"],
                },
            )

            user.first_name = user_data["first_name"]
            user.last_name = user_data["last_name"]
            user.email = user_data["email"]
            user.set_password(self.DEFAULT_PASSWORD)
            user.save()

            action = "created" if created else "updated"
            self.stdout.write(
                self.style.SUCCESS(
                    f" - {user.username} ({user.get_full_name() or user.username}) [{action}]"
                )
            )

        owner = user_model.objects.get(username="aleix")
        Group.objects.filter(name="Aleix Demo Squad", owner=owner).update(name="Aleix Demo Group")
        group, group_created = Group.objects.get_or_create(
            name="Aleix Demo Group",
            owner=owner,
            defaults={
                "description": "Local group for testing Choosy plan creation.",
                "mission_statement": "Pick the plan with the least friction.",
                "interests": ["food", "culture", "outdoors"],
            },
        )
        group.add_member(user=owner, role=GroupMember.Role.OWNER)
        proposal = PlanProposal.objects.filter(
            group=group,
            status__in=[PlanProposal.Status.DRAFT, PlanProposal.Status.VOTING],
        ).first()
        proposal_created = proposal is None
        if proposal is None:
            proposal = PlanProposal.objects.create(
                group=group,
                created_by=owner,
                status=PlanProposal.Status.VOTING,
                title="Weekend Demo Vote",
                description="Use this proposal to test location search and weather.",
            )
        self.stdout.write("")
        self.stdout.write(
            self.style.SUCCESS(
                f"Demo group ready: {group.name} [{'created' if group_created else 'existing'}]"
            )
        )
        self.stdout.write(
            self.style.SUCCESS(
                f"Demo proposal ready: {proposal.title} [{'created' if proposal_created else 'existing'}]"
            )
        )

        self.stdout.write("")
        self.stdout.write(
            self.style.WARNING(
                f"Demo password for all seeded users: {self.DEFAULT_PASSWORD}"
            )
        )
