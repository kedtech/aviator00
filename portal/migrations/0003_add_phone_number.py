# Generated manually for phone_number field

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("portal", "0002_demosession_reviewed_at_alter_demosession_status"),
    ]

    operations = [
        migrations.AddField(
            model_name="demosession",
            name="phone_number",
            field=models.CharField(blank=True, max_length=20),
        ),
    ]
