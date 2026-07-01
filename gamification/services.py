from django.db import models, transaction
from django.urls import reverse

from accounts.models import StudentProfile
from certificates.models import Certificate
from certificates.services import ensure_certificate_assets
from gamification.models import Badge, Leaderboard, LearningStreak, PointsTransaction, UserBadge
from notifications.models import Notification


LESSON_POINTS = 10
QUIZ_PASS_POINTS = 25
COURSE_COMPLETION_POINTS = 100
CERTIFICATE_POINTS = 50
LEVEL_POINTS = 100


def _total_points(user):
    return PointsTransaction.objects.filter(user=user).aggregate(total=models.Sum("points"))["total"] or 0


def _sync_student_profile(user, total):
    if not getattr(user, "is_student", False):
        return None
    profile, _ = StudentProfile.objects.get_or_create(user=user)
    profile.points = max(total, 0)
    profile.level = max(1, int(profile.points / LEVEL_POINTS) + 1)
    profile.save(update_fields=["points", "level"])
    return profile


def _sync_leaderboard(user):
    total = _total_points(user)
    Leaderboard.objects.update_or_create(user=user, defaults={"points": max(total, 0)})
    _sync_student_profile(user, total)
    for index, entry in enumerate(Leaderboard.objects.order_by("-points", "user__email"), start=1):
        if entry.rank != index:
            entry.rank = index
            entry.save(update_fields=["rank", "updated_at"])
    return total


def _record_streak(user):
    streak, _ = LearningStreak.objects.get_or_create(user=user)
    streak.record_activity()
    return streak


def _award_badges(user, total_points):
    earned = []
    badges = Badge.objects.filter(is_active=True, points_required__lte=total_points)
    for badge in badges:
        user_badge, created = UserBadge.objects.get_or_create(user=user, badge=badge)
        if created:
            earned.append(user_badge)
            Notification.objects.get_or_create(
                user=user,
                title=f"Badge earned: {badge.name}",
                notification_type=Notification.Type.SYSTEM,
                link=reverse("gamification:achievements"),
                defaults={"message": f"You earned the {badge.name} badge."},
            )
    return earned


@transaction.atomic
def award_points(user, points, reason, description, unique=True):
    if unique and PointsTransaction.objects.filter(user=user, reason=reason, description=description).exists():
        return None
    transaction = PointsTransaction.objects.create(
        user=user,
        points=points,
        reason=reason,
        description=description[:180],
    )
    _record_streak(user)
    total = _sync_leaderboard(user)
    _award_badges(user, total)
    return transaction


def sync_user_xp(user):
    total = _sync_leaderboard(user)
    _award_badges(user, total)
    return total


def rebuild_xp_state():
    users = {transaction.user for transaction in PointsTransaction.objects.select_related("user")}
    results = []
    for user in users:
        results.append((user.email, sync_user_xp(user)))
    return results


def record_lesson_completion(user, lesson):
    return award_points(
        user=user,
        points=LESSON_POINTS,
        reason=PointsTransaction.Reason.LESSON_COMPLETED,
        description=f"lesson_completed:{lesson.id}",
    )


def record_quiz_passed(user, quiz):
    transaction = award_points(
        user=user,
        points=QUIZ_PASS_POINTS,
        reason=PointsTransaction.Reason.QUIZ_PASSED,
        description=f"quiz_passed:{quiz.id}",
    )
    if transaction:
        Notification.objects.get_or_create(
            user=user,
            title="Quiz passed",
            notification_type=Notification.Type.SYSTEM,
            link=quiz.course.get_absolute_url(),
            defaults={"message": f"You passed {quiz.title} and earned {QUIZ_PASS_POINTS} points."},
        )
    return transaction


def record_course_completion(request, enrollment):
    course = enrollment.course
    course_transaction = award_points(
        user=enrollment.student,
        points=COURSE_COMPLETION_POINTS,
        reason=PointsTransaction.Reason.COURSE_COMPLETED,
        description=f"course_completed:{course.id}",
    )
    if course_transaction:
        Notification.objects.get_or_create(
            user=enrollment.student,
            title="Course completed",
            notification_type=Notification.Type.SYSTEM,
            link=course.get_absolute_url(),
            defaults={"message": f"You completed {course.title} and earned {COURSE_COMPLETION_POINTS} points."},
        )

    certificate = None
    if course.certificate_available:
        certificate, created = Certificate.objects.get_or_create(
            student=enrollment.student,
            course=course,
            defaults={"instructor_name": course.instructor.get_full_name() or course.instructor.username},
        )
        if created:
            award_points(
                user=enrollment.student,
                points=CERTIFICATE_POINTS,
                reason=PointsTransaction.Reason.CERTIFICATE_EARNED,
                description=f"certificate_earned:{course.id}",
            )
            Notification.objects.get_or_create(
                user=enrollment.student,
                title="Certificate earned",
                notification_type=Notification.Type.CERTIFICATE,
                link=reverse("certificates:detail", kwargs={"certificate_id": certificate.certificate_id}),
                defaults={"message": f"Your certificate for {course.title} is ready."},
            )
        ensure_certificate_assets(request, certificate)
    return certificate