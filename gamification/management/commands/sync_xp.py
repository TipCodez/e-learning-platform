from django.core.management.base import BaseCommand

from gamification.services import rebuild_xp_state


class Command(BaseCommand):
    help = "Rebuild leaderboard ranks, student XP profiles, and badge awards from point transactions."

    def handle(self, *args, **options):
        results = rebuild_xp_state()
        self.stdout.write(self.style.SUCCESS(f"Synced XP for {len(results)} users."))
        for email, points in results:
            self.stdout.write(f"{email}: {points} points")