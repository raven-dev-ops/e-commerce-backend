"""Management command to purge inactive user accounts."""

from django.core.management.base import BaseCommand
from users.tasks import perform_user_purge


class Command(BaseCommand):
    help = "Delete inactive users beyond the retention window."

    def handle(self, *args, **options):
        deleted = perform_user_purge()
        self.stdout.write(self.style.SUCCESS(f"Purged {deleted} inactive users."))
