from decimal import Decimal

from django.core.management.base import BaseCommand
from django.db import transaction

from accounts.models import CustomUser
from assessments.models import AnswerOption, Question, Quiz
from courses.models import Category, Course, Lesson, Module, SubCategory
from gamification.models import Badge
from learning_paths.models import LearningPath, LearningPathCourse
from payments.models import SubscriptionPlan


class Command(BaseCommand):
    help = "Seed Acadeval with demo catalog, badges, plans, and learning paths."

    @transaction.atomic
    def handle(self, *args, **options):
        instructor = self._instructor()
        categories = self._categories()
        courses = self._courses(instructor, categories)
        self._learning_paths(courses)
        self._badges()
        self._plans()
        self.stdout.write(self.style.SUCCESS("Acadeval demo data is ready."))

    def _instructor(self):
        user, created = CustomUser.objects.get_or_create(
            username="demo_instructor",
            defaults={
                "email": "instructor@acadeval.local",
                "first_name": "Acadeval",
                "last_name": "Instructor",
                "role": CustomUser.Role.INSTRUCTOR,
                "terms_accepted": True,
                "email_verified": True,
            },
        )
        if created:
            user.set_password("DemoPass123!")
            user.save(update_fields=["password"])
        return user

    def _categories(self):
        data = {
            "Technology": ["Web Development", "Cybersecurity", "AI Tools"],
            "Business": ["Entrepreneurship", "Digital Marketing"],
            "Creative Skills": ["Graphic Design", "Content Creation"],
            "Career Development": ["CV Writing", "Interview Preparation"],
        }
        categories = {}
        for category_name, subcategories in data.items():
            category, _ = Category.objects.get_or_create(
                name=category_name,
                defaults={"description": f"Practical {category_name.lower()} courses for career growth."},
            )
            categories[category_name] = category
            for subcategory_name in subcategories:
                SubCategory.objects.get_or_create(
                    category=category,
                    name=subcategory_name,
                    defaults={"description": f"{subcategory_name} learning track."},
                )
        return categories

    def _courses(self, instructor, categories):
        specs = [
            {
                "title": "Python Fundamentals for Beginners",
                "category": "Technology",
                "subcategory": "Web Development",
                "level": Course.Level.BEGINNER,
                "duration": "6 weeks",
                "price": Decimal("0.00"),
                "is_free": True,
                "description": "Learn Python syntax, problem solving, functions, files, and practical mini projects.",
            },
            {
                "title": "Digital Marketing Essentials",
                "category": "Business",
                "subcategory": "Digital Marketing",
                "level": Course.Level.INTERMEDIATE,
                "duration": "4 weeks",
                "price": Decimal("120.00"),
                "is_free": False,
                "description": "Plan campaigns, understand audiences, build content funnels, and measure performance.",
            },
            {
                "title": "Cybersecurity Foundations",
                "category": "Technology",
                "subcategory": "Cybersecurity",
                "level": Course.Level.BEGINNER,
                "duration": "5 weeks",
                "price": Decimal("150.00"),
                "is_free": False,
                "description": "Understand threats, passwords, networks, phishing, and basic defensive practices.",
            },
            {
                "title": "Graphic Design with Canva",
                "category": "Creative Skills",
                "subcategory": "Graphic Design",
                "level": Course.Level.BEGINNER,
                "duration": "3 weeks",
                "price": Decimal("0.00"),
                "is_free": True,
                "description": "Create clean social media graphics, flyers, presentations, and brand templates.",
            },
        ]
        courses = {}
        for spec in specs:
            category = categories[spec["category"]]
            subcategory = SubCategory.objects.get(category=category, name=spec["subcategory"])
            course, _ = Course.objects.update_or_create(
                title=spec["title"],
                defaults={
                    "instructor": instructor,
                    "category": category,
                    "subcategory": subcategory,
                    "subtitle": spec["description"][:180],
                    "description": spec["description"],
                    "learning_outcomes": "Build practical skills\nComplete guided exercises\nPrepare for assessment",
                    "requirements": "A laptop or smartphone and internet access.",
                    "target_audience": "Students, job seekers, professionals, and self-paced learners.",
                    "level": spec["level"],
                    "duration": spec["duration"],
                    "price": spec["price"],
                    "is_free": spec["is_free"],
                    "certificate_available": True,
                    "featured": True,
                    "popular": True,
                    "status": Course.Status.PUBLISHED,
                },
            )
            courses[spec["title"]] = course
            self._course_content(course)
        return courses

    def _course_content(self, course):
        module, _ = Module.objects.get_or_create(
            course=course,
            order=1,
            defaults={"title": "Getting Started", "description": "Core concepts and first practical steps."},
        )
        Lesson.objects.get_or_create(
            module=module,
            order=1,
            defaults={
                "title": "Welcome and Course Roadmap",
                "lesson_type": Lesson.LessonType.TEXT,
                "content": "Welcome to the course. Review the outcomes, complete each lesson, and take the quiz.",
                "duration_minutes": 8,
                "is_preview": True,
            },
        )
        Lesson.objects.get_or_create(
            module=module,
            order=2,
            defaults={
                "title": "Practical Exercise",
                "lesson_type": Lesson.LessonType.TEXT,
                "content": "Apply the main concept from this module in a small hands-on task.",
                "duration_minutes": 20,
            },
        )
        quiz, _ = Quiz.objects.get_or_create(
            course=course,
            title=f"{course.title} Knowledge Check",
            defaults={"description": "A short auto-marked quiz.", "pass_mark": 70, "retake_limit": 3},
        )
        question, _ = Question.objects.get_or_create(
            quiz=quiz,
            order=1,
            defaults={"text": "What is the best way to complete this course?", "points": 1},
        )
        AnswerOption.objects.get_or_create(question=question, text="Skip the exercises", defaults={"is_correct": False})
        AnswerOption.objects.get_or_create(question=question, text="Practice each lesson and take assessments", defaults={"is_correct": True})

    def _learning_paths(self, courses):
        path_specs = [
            ("Become a Web Developer", ["Python Fundamentals for Beginners"]),
            ("Become a Cybersecurity Beginner", ["Cybersecurity Foundations"]),
            ("Digital Marketing Career Path", ["Digital Marketing Essentials"]),
            ("Graphic Design with Canva", ["Graphic Design with Canva"]),
        ]
        for title, course_titles in path_specs:
            path, _ = LearningPath.objects.get_or_create(
                title=title,
                defaults={
                    "description": f"A structured path to help learners {title.lower()}.",
                    "career_outcome": title,
                    "estimated_duration": "4-10 weeks",
                    "is_featured": True,
                },
            )
            for index, course_title in enumerate(course_titles, start=1):
                LearningPathCourse.objects.get_or_create(
                    learning_path=path,
                    course=courses[course_title],
                    defaults={"order": index, "is_required": True},
                )

    def _badges(self):
        badges = [
            ("First Course Started", 10),
            ("First Lesson Completed", 25),
            ("Quiz Master", 100),
            ("Certificate Earner", 250),
            ("7-Day Learning Streak", 350),
            ("Top Learner", 500),
            ("Career Builder", 150),
            ("Fast Finisher", 300),
        ]
        for name, points in badges:
            Badge.objects.get_or_create(
                name=name,
                defaults={
                    "description": f"Earned when a learner reaches the {name.lower()} milestone.",
                    "points_required": points,
                    "is_active": True,
                },
            )

    def _plans(self):
        plans = [
            ("Free Learner", Decimal("0.00"), 30, "Browse free courses and earn certificates for free tracks."),
            ("Pro Learner", Decimal("49.00"), 30, "Access premium learning support and advanced career tools."),
            ("Organization", Decimal("499.00"), 30, "Manage teams, learner reports, billing, and certificates."),
        ]
        for name, price, days, description in plans:
            SubscriptionPlan.objects.get_or_create(
                name=name,
                defaults={"price": price, "duration_days": days, "description": description, "is_active": True},
            )
