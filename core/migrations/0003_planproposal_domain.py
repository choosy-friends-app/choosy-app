import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models
from django.db.models import Q


def migrate_plans_to_proposals(apps, schema_editor):
    Group = apps.get_model("core", "Group")
    Plan = apps.get_model("core", "Plan")
    PlanProposal = apps.get_model("core", "PlanProposal")

    open_statuses = {"draft", "voting"}

    for group in Group.objects.all():
        group_plans = list(Plan.objects.filter(group=group).order_by("created_at", "id"))
        if not group_plans:
            continue

        open_plans = [plan for plan in group_plans if plan.status in open_statuses]
        migrated_plan_ids = set()

        if open_plans:
            proposal_title = open_plans[0].title if len(open_plans) == 1 else f"{group.name} voting round"
            proposal_description = next((plan.description for plan in open_plans if plan.description), "")
            proposal = PlanProposal.objects.create(
                group=group,
                created_by=open_plans[0].created_by,
                title=proposal_title[:120],
                description=proposal_description[:255],
                status="voting" if any(plan.status == "voting" for plan in open_plans) else "draft",
            )

            for order, plan in enumerate(open_plans, start=1):
                plan.proposal_id = proposal.id
                plan.option_order = order
                plan.status = "proposed"
                plan.save(update_fields=["proposal", "option_order", "status"])
                migrated_plan_ids.add(plan.id)

        for plan in group_plans:
            if plan.id in migrated_plan_ids:
                continue

            proposal_status = {
                "draft": "draft",
                "voting": "voting",
                "chosen": "chosen",
                "cancelled": "cancelled",
            }.get(plan.status, "voting")

            proposal = PlanProposal.objects.create(
                group=group,
                created_by=plan.created_by,
                title=plan.title[:120],
                description=plan.description[:255],
                status=proposal_status,
            )

            plan.proposal_id = proposal.id
            plan.option_order = 1
            plan.status = "chosen" if plan.status == "chosen" else "proposed"
            plan.save(update_fields=["proposal", "option_order", "status"])

            if proposal_status == "chosen":
                proposal.chosen_plan_id = plan.id
                proposal.save(update_fields=["chosen_plan"])

        if PlanProposal.objects.filter(group=group, status="voting").exists():
            group.status = "voting"
            group.save(update_fields=["status"])


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0002_groupmember_identity_fields"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="PlanProposal",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("title", models.CharField(max_length=120)),
                ("description", models.CharField(blank=True, max_length=255)),
                ("voting_ends_at", models.DateTimeField(blank=True, null=True)),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("draft", "Draft"),
                            ("voting", "Voting"),
                            ("chosen", "Chosen"),
                            ("cancelled", "Cancelled"),
                        ],
                        default="voting",
                        max_length=20,
                    ),
                ),
                (
                    "created_by",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="created_plan_proposals",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "group",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="proposals",
                        to="core.group",
                    ),
                ),
                (
                    "chosen_plan",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="chosen_for_proposals",
                        to="core.plan",
                    ),
                ),
            ],
            options={
                "ordering": ["-created_at"],
            },
        ),
        migrations.AddField(
            model_name="plan",
            name="option_order",
            field=models.PositiveSmallIntegerField(default=0),
        ),
        migrations.AddField(
            model_name="plan",
            name="proposal",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="plans",
                to="core.planproposal",
            ),
        ),
        migrations.AlterField(
            model_name="plan",
            name="status",
            field=models.CharField(
                choices=[
                    ("proposed", "Proposed"),
                    ("shortlisted", "Shortlisted"),
                    ("chosen", "Chosen"),
                    ("archived", "Archived"),
                ],
                default="proposed",
                max_length=20,
            ),
        ),
        migrations.RunPython(migrate_plans_to_proposals, migrations.RunPython.noop),
        migrations.AlterField(
            model_name="plan",
            name="proposal",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="plans",
                to="core.planproposal",
            ),
        ),
        migrations.AddIndex(
            model_name="planproposal",
            index=models.Index(fields=["group", "status"], name="core_planpr_group_i_5fcca1_idx"),
        ),
        migrations.AddIndex(
            model_name="planproposal",
            index=models.Index(fields=["status", "created_at"], name="core_planpr_status_0c8fb5_idx"),
        ),
        migrations.AddConstraint(
            model_name="planproposal",
            constraint=models.UniqueConstraint(
                condition=Q(("status__in", ["draft", "voting"])),
                fields=("group",),
                name="unique_open_proposal_per_group",
            ),
        ),
        migrations.RemoveIndex(
            model_name="plan",
            name="core_plan_status_627444_idx",
        ),
        migrations.AddIndex(
            model_name="plan",
            index=models.Index(fields=["proposal", "option_order"], name="core_plan_proposa_528a32_idx"),
        ),
        migrations.AddConstraint(
            model_name="plan",
            constraint=models.UniqueConstraint(
                fields=("proposal", "option_order"),
                name="unique_plan_option_order_per_proposal",
            ),
        ),
    ]
