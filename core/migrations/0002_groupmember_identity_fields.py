import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


def migrate_groupmember_roles(apps, schema_editor):
    Group = apps.get_model("core", "Group")
    GroupMember = apps.get_model("core", "GroupMember")

    for member in GroupMember.objects.all():
        role = "admin" if getattr(member, "is_admin", False) else "member"
        if member.user_id and Group.objects.filter(id=member.group_id, owner_id=member.user_id).exists():
            role = "owner"
        member.role = role
        member.status = "active"
        if member.display_name == "" and member.user_id:
            user = member.user
            member.display_name = user.get_full_name() or user.get_username()
        member.save(update_fields=["role", "status", "display_name"])


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0001_initial"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name="groupmember",
            name="role",
            field=models.CharField(
                choices=[("owner", "Owner"), ("admin", "Admin"), ("member", "Member")],
                default="member",
                max_length=16,
            ),
        ),
        migrations.AddField(
            model_name="groupmember",
            name="status",
            field=models.CharField(
                choices=[("invited", "Invited"), ("active", "Active"), ("left", "Left")],
                default="active",
                max_length=16,
            ),
        ),
        migrations.AddField(
            model_name="groupmember",
            name="invited_by",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="sent_group_invites",
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        migrations.RunPython(migrate_groupmember_roles, migrations.RunPython.noop),
        migrations.RemoveField(
            model_name="groupmember",
            name="is_admin",
        ),
    ]
