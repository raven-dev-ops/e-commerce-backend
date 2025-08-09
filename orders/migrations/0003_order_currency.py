from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        (
            "orders",
            "0002_alter_order_created_at_alter_order_payment_intent_id_and_more",
        ),
    ]

    operations = [
        migrations.AddField(
            model_name="order",
            name="currency",
            field=models.CharField(default="usd", max_length=3),
        ),
    ]
