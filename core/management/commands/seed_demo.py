from decimal import Decimal

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from accounts.models import CustomUser
from assessments.models import AnswerOption, Assignment, AssignmentSubmission, Question, Quiz
from core.models import BlogContentBlock, BlogPost, FAQ
from courses.models import Category, Course, Lesson, LessonContentBlock, Module, Review, SubCategory
from discussions.models import Announcement, Discussion, DiscussionReply, DiscussionVote
from enrollments.models import CourseProgress, Enrollment, LessonProgress
from gamification.models import Badge, PointsTransaction
from gamification.services import award_points, sync_user_xp
from learning_paths.models import LearningPath, LearningPathCourse
from organizations.models import OrganizationEnrollment, OrganizationLearner, OrganizationReport
from payments.models import Coupon, Invoice, Payment, SubscriptionPlan


class Command(BaseCommand):
    help = "Seed Acadeval with rich demo courses, content blocks, org data, payments, blogs, and engagement data."

    @transaction.atomic
    def handle(self, *args, **options):
        users = self._users()
        categories = self._categories()
        courses = self._courses(users["instructor"], categories)
        self._learning_paths(courses)
        self._badges()
        self._plans_and_coupons()
        self._organization(users, courses)
        self._payments(users, courses)
        self._engagement(users, courses)
        self._content(users["instructor"])
        self.stdout.write(self.style.SUCCESS("Acadeval rich demo data is ready."))

    def _user(self, username, email, role, first_name, last_name):
        user, _ = CustomUser.objects.update_or_create(
            email=email,
            defaults={
                "username": username,
                "first_name": first_name,
                "last_name": last_name,
                "role": role,
                "terms_accepted": True,
                "email_verified": True,
            },
        )
        user.set_password("DemoPass123!")
        user.save(update_fields=["password"])
        return user

    def _users(self):
        instructor = self._user("demo_instructor", "instructor@acadeval.local", CustomUser.Role.INSTRUCTOR, "Acadeval", "Instructor")
        second_instructor = self._user("demo_mentor", "mentor@acadeval.local", CustomUser.Role.INSTRUCTOR, "Nana", "Mentor")
        learner = self._user("demo_learner", "learner@acadeval.local", CustomUser.Role.STUDENT, "Ama", "Learner")
        learner_two = self._user("demo_colleague", "colleague@acadeval.local", CustomUser.Role.STUDENT, "Kofi", "Colleague")
        organization = self._user("demo_org", "org@acadeval.local", CustomUser.Role.ORGANIZATION, "Acadeval", "Teams")
        return {
            "instructor": instructor,
            "mentor": second_instructor,
            "learner": learner,
            "learner_two": learner_two,
            "organization": organization,
        }

    def _categories(self):
        data = {
            "Technology": ["Web Development", "Cybersecurity", "AI Tools", "Data Analytics"],
            "Business": ["Entrepreneurship", "Digital Marketing", "Project Management"],
            "Creative Skills": ["Graphic Design", "Content Creation", "Video Editing"],
            "Career Development": ["CV Writing", "Interview Preparation", "Workplace Communication"],
        }
        categories = {}
        for category_name, subcategories in data.items():
            category, _ = Category.objects.update_or_create(
                name=category_name,
                defaults={"description": f"Practical {category_name.lower()} courses for career growth.", "is_active": True},
            )
            categories[category_name] = category
            for subcategory_name in subcategories:
                SubCategory.objects.update_or_create(
                    category=category,
                    name=subcategory_name,
                    defaults={"description": f"{subcategory_name} learning track."},
                )
        return categories

    def _courses(self, instructor, categories):
        specs = [
            ("Python Fundamentals for Beginners", "Technology", "Web Development", Course.Level.BEGINNER, "6 weeks", "0.00", True, "Learn Python syntax, problem solving, functions, files, and practical mini projects."),
            ("Career-Ready Web Development", "Technology", "Web Development", Course.Level.BEGINNER, "10 weeks", "250.00", False, "Build responsive pages, reusable UI patterns, Django views, and deployable portfolio projects."),
            ("Data Analytics with Spreadsheets", "Technology", "Data Analytics", Course.Level.BEGINNER, "5 weeks", "90.00", False, "Clean datasets, build formulas, create dashboards, and communicate insights with charts."),
            ("AI Tools for Work Productivity", "Technology", "AI Tools", Course.Level.INTERMEDIATE, "3 weeks", "80.00", False, "Use AI assistants safely for drafting, research, planning, summaries, and workflow automation."),
            ("Digital Marketing Essentials", "Business", "Digital Marketing", Course.Level.INTERMEDIATE, "4 weeks", "120.00", False, "Plan campaigns, understand audiences, build content funnels, and measure performance."),
            ("Project Management Starter Kit", "Business", "Project Management", Course.Level.BEGINNER, "4 weeks", "110.00", False, "Scope projects, manage tasks, communicate risks, and run lightweight delivery ceremonies."),
            ("Cybersecurity Foundations", "Technology", "Cybersecurity", Course.Level.BEGINNER, "5 weeks", "150.00", False, "Understand threats, passwords, networks, phishing, and basic defensive practices."),
            ("Graphic Design with Canva", "Creative Skills", "Graphic Design", Course.Level.BEGINNER, "3 weeks", "0.00", True, "Create clean social media graphics, flyers, presentations, and brand templates."),
            ("Content Creation for Educators", "Creative Skills", "Content Creation", Course.Level.INTERMEDIATE, "4 weeks", "75.00", False, "Plan lessons, write scripts, record learning videos, and package resources for students."),
            ("Interview Preparation Bootcamp", "Career Development", "Interview Preparation", Course.Level.BEGINNER, "2 weeks", "0.00", True, "Prepare confident answers, build STAR stories, and practice role-specific interview questions."),
        ]
        courses = {}
        for index, (title, category_name, subcategory_name, level, duration, price, is_free, description) in enumerate(specs, start=1):
            category = categories[category_name]
            subcategory = SubCategory.objects.get(category=category, name=subcategory_name)
            course, _ = Course.objects.update_or_create(
                title=title,
                defaults={
                    "instructor": instructor,
                    "category": category,
                    "subcategory": subcategory,
                    "subtitle": description[:180],
                    "description": description,
                    "learning_outcomes": "Build practical skills\nComplete guided exercises\nPrepare for assessment\nEarn a verifiable certificate",
                    "requirements": "A laptop or smartphone, internet access, and a willingness to practice.",
                    "target_audience": "Students, job seekers, professionals, organizations, and self-paced learners.",
                    "level": level,
                    "duration": duration,
                    "price": Decimal(price),
                    "is_free": is_free,
                    "certificate_available": True,
                    "featured": index <= 6,
                    "popular": index <= 8,
                    "status": Course.Status.PUBLISHED,
                    "approved_at": timezone.now(),
                },
            )
            courses[title] = course
            self._course_content(course, index)
        return courses

    def _course_content(self, course, seed_index):
        module_specs = [
            (1, "Getting Started", "Orientation, outcomes, and the first practical workflow."),
            (2, "Hands-on Practice", "Guided examples, resources, and a graded assignment."),
        ]
        lessons = []
        for module_order, module_title, module_description in module_specs:
            module, _ = Module.objects.update_or_create(
                course=course,
                order=module_order,
                defaults={"title": module_title, "description": module_description},
            )
            lesson, _ = Lesson.objects.update_or_create(
                module=module,
                order=1,
                defaults={
                    "title": f"{module_title} Roadmap",
                    "lesson_type": Lesson.LessonType.TEXT,
                    "content": "Legacy fallback content for this lesson. Rich blocks are rendered when available.",
                    "duration_minutes": 10 + module_order,
                    "is_preview": module_order == 1,
                },
            )
            lessons.append(lesson)
            self._lesson_blocks(lesson, course, module_order)

            exercise, _ = Lesson.objects.update_or_create(
                module=module,
                order=2,
                defaults={
                    "title": f"{module_title} Practical Exercise",
                    "lesson_type": Lesson.LessonType.TEXT,
                    "content": "Complete the exercise, save your notes, and mark the lesson complete.",
                    "duration_minutes": 20 + module_order,
                },
            )
            lessons.append(exercise)
            self._lesson_blocks(exercise, course, module_order + 10)

        quiz, _ = Quiz.objects.update_or_create(
            course=course,
            title=f"{course.title} Knowledge Check",
            defaults={"description": "A short auto-marked quiz.", "pass_mark": 70, "retake_limit": 3, "time_limit_minutes": 10},
        )
        questions = [
            (1, "What is the best way to complete this course?", "Practice each lesson and take assessments"),
            (2, "What should you do when a concept feels unclear?", "Use notes, discussions, and examples to review it"),
        ]
        for order, text, correct in questions:
            question, _ = Question.objects.update_or_create(quiz=quiz, order=order, defaults={"text": text, "points": 1})
            AnswerOption.objects.update_or_create(question=question, text=correct, defaults={"is_correct": True})
            AnswerOption.objects.update_or_create(question=question, text="Skip the practice and move on", defaults={"is_correct": False})

        Assignment.objects.update_or_create(
            course=course,
            title=f"{course.title} Portfolio Task",
            defaults={
                "lesson": lessons[-1],
                "instructions": "Submit a short reflection, screenshot, or link that proves you completed the main practical task.",
                "max_score": 100,
            },
        )

    def _lesson_blocks(self, lesson, course, variant):
        lesson.content_blocks.all().delete()
        blocks = [
            (1, LessonContentBlock.BlockType.SUBTITLE, "Lesson goals", "", ""),
            (2, LessonContentBlock.BlockType.SECTION, "What you will build", "Follow a practical sequence", f"This lesson connects directly to {course.title}. Read the steps, try the example, and save notes as you go."),
            (3, LessonContentBlock.BlockType.CODE, "", "python", f"task = \"{course.title}\"\nprint(f\"Practice: {{task}}\")"),
            (4, LessonContentBlock.BlockType.OUTPUT, "Expected output", "", f"Practice: {course.title}"),
            (5, LessonContentBlock.BlockType.TABLE, "Checklist", "", "Step|Action|Done\n1|Review the concept|No\n2|Try the example|No\n3|Save lesson notes|No"),
            (6, LessonContentBlock.BlockType.TILE, "Practice tip", "Make it visible", "Keep one small artifact from every lesson: a note, screenshot, link, or code snippet."),
            (7, LessonContentBlock.BlockType.CALLOUT, "Remember", "", "Use the course discussion area when you need clarification from the instructor or peers."),
        ]
        for order, block_type, title, subtitle, body in blocks:
            LessonContentBlock.objects.create(
                lesson=lesson,
                order=order,
                block_type=block_type,
                title=title,
                subtitle=subtitle if block_type != LessonContentBlock.BlockType.CODE else "",
                body=body,
                code_language="python" if block_type == LessonContentBlock.BlockType.CODE else "",
                table_data=body if block_type == LessonContentBlock.BlockType.TABLE else "",
            )

    def _learning_paths(self, courses):
        path_specs = [
            ("Full Stack Starter", ["Python Fundamentals for Beginners", "Career-Ready Web Development"]),
            ("Digital Growth Specialist", ["Digital Marketing Essentials", "Content Creation for Educators"]),
            ("Workplace Productivity Path", ["AI Tools for Work Productivity", "Project Management Starter Kit"]),
            ("Cybersecurity Beginner Path", ["Cybersecurity Foundations"]),
            ("Career Launch Path", ["Interview Preparation Bootcamp", "Graphic Design with Canva"]),
        ]
        for title, course_titles in path_specs:
            path, _ = LearningPath.objects.update_or_create(
                title=title,
                defaults={
                    "description": f"A structured path for {title.lower()} with courses, assessments, and certificates.",
                    "career_outcome": title,
                    "estimated_duration": "4-12 weeks",
                    "is_featured": True,
                },
            )
            for index, course_title in enumerate(course_titles, start=1):
                LearningPathCourse.objects.update_or_create(
                    learning_path=path,
                    course=courses[course_title],
                    defaults={"order": index, "is_required": True},
                )

    def _badges(self):
        badges = [
            ("First Course Started", 10),
            ("First Lesson Completed", 25),
            ("Quiz Master", 100),
            ("Career Builder", 150),
            ("Certificate Earner", 250),
            ("Fast Finisher", 300),
            ("7-Day Learning Streak", 350),
            ("Top Learner", 500),
            ("Organization Learner", 650),
            ("Portfolio Ready", 800),
        ]
        for name, points in badges:
            Badge.objects.update_or_create(
                name=name,
                defaults={"description": f"Earned when a learner reaches the {name.lower()} milestone.", "points_required": points, "is_active": True},
            )

    def _plans_and_coupons(self):
        plans = [
            ("Free Learner", "0.00", 30, "Browse free courses and earn certificates for free tracks."),
            ("Pro Learner", "49.00", 30, "Access premium learning support and advanced career tools."),
            ("Organization", "499.00", 30, "Manage teams, learner reports, billing, and certificates."),
        ]
        for name, price, days, description in plans:
            SubscriptionPlan.objects.update_or_create(name=name, defaults={"price": Decimal(price), "duration_days": days, "description": description, "is_active": True})
        Coupon.objects.update_or_create(
            code="WELCOME25",
            defaults={"discount_percent": 25, "valid_from": timezone.now(), "valid_until": timezone.now() + timezone.timedelta(days=90), "usage_limit": 250, "is_active": True},
        )
        Coupon.objects.update_or_create(
            code="ORGTEAM40",
            defaults={"discount_percent": 40, "valid_from": timezone.now(), "valid_until": timezone.now() + timezone.timedelta(days=90), "usage_limit": 100, "is_active": True},
        )

    def _organization(self, users, courses):
        organization = users["organization"]
        learners = [users["learner"], users["learner_two"]]
        for index, learner in enumerate(learners, start=1):
            OrganizationLearner.objects.update_or_create(
                organization=organization,
                learner=learner,
                defaults={"department": "Training" if index == 1 else "Marketing", "active": True},
            )
        course = courses["AI Tools for Work Productivity"]
        org_enrollment, _ = OrganizationEnrollment.objects.get_or_create(organization=organization, course=course)
        org_enrollment.learners.set(learners)
        for learner in learners:
            enrollment, _ = Enrollment.objects.get_or_create(student=learner, course=course)
            CourseProgress.objects.get_or_create(enrollment=enrollment)
        OrganizationReport.objects.update_or_create(
            organization=organization,
            title="Demo organization training report",
            defaults={"summary": "Learners: 2\nEnrollments: 2\nCompleted enrollments: 0\nCourses represented: 1"},
        )

    def _payments(self, users, courses):
        paid_courses = [courses["Career-Ready Web Development"], courses["Digital Marketing Essentials"], courses["AI Tools for Work Productivity"]]
        for index, course in enumerate(paid_courses, start=1):
            payment, _ = Payment.objects.update_or_create(
                reference=f"DEMO-PAY-{index}",
                defaults={
                    "user": users["learner"],
                    "course": course,
                    "amount": course.price,
                    "gateway": Payment.Gateway.CARD,
                    "status": Payment.Status.SUCCESS,
                    "paid_at": timezone.now(),
                    "provider_response": {"mode": "seed_demo"},
                },
            )
            Invoice.objects.update_or_create(
                payment=payment,
                defaults={"invoice_number": f"DEMO-INV-{index}", "billing_name": users["learner"].get_full_name(), "billing_email": users["learner"].email},
            )
            enrollment, _ = Enrollment.objects.get_or_create(student=users["learner"], course=course)
            CourseProgress.objects.get_or_create(enrollment=enrollment)

    def _engagement(self, users, courses):
        learner = users["learner"]
        instructor = users["instructor"]
        for course in list(courses.values())[:4]:
            enrollment, _ = Enrollment.objects.get_or_create(student=learner, course=course)
            progress, _ = CourseProgress.objects.get_or_create(enrollment=enrollment)
            first_lesson = Lesson.objects.filter(module__course=course).first()
            if first_lesson:
                lesson_progress, _ = LessonProgress.objects.get_or_create(enrollment=enrollment, lesson=first_lesson)
                if not lesson_progress.completed:
                    lesson_progress.mark_complete()
                progress.recalculate()
            Review.objects.update_or_create(course=course, user=learner, defaults={"rating": 5, "comment": "Clear, practical, and easy to follow.", "is_approved": True})
            discussion, _ = Discussion.objects.update_or_create(
                course=course,
                author=learner,
                title=f"How should I practice {course.title}?",
                defaults={"body": "I completed the roadmap lesson. What should I focus on next?", "is_hidden": False},
            )
            DiscussionReply.objects.update_or_create(
                discussion=discussion,
                author=instructor,
                defaults={"body": "Start with the practical exercise, save notes, and submit the portfolio task.", "is_instructor_reply": True},
            )
            DiscussionVote.objects.get_or_create(discussion=discussion, user=learner)
            discussion.upvotes = discussion.votes.count()
            discussion.save(update_fields=["upvotes"])
            Announcement.objects.update_or_create(
                course=course,
                title=f"Welcome to {course.title}",
                defaults={"author": instructor, "body": "This course now includes rich lesson blocks, assessments, discussions, and certificates."},
            )
        assignment = Assignment.objects.filter(course=courses["Python Fundamentals for Beginners"]).first()
        if assignment:
            AssignmentSubmission.objects.update_or_create(
                assignment=assignment,
                student=learner,
                defaults={"response_text": "I completed the Python mini project and documented the key steps.", "score": Decimal("92.00"), "feedback": "Strong work. Good structure and clear reflection.", "graded_by": instructor, "graded_at": timezone.now()},
            )
        award_points(learner, 10, PointsTransaction.Reason.LESSON_COMPLETED, "seed_demo_lesson", unique=True)
        award_points(learner, 25, PointsTransaction.Reason.QUIZ_PASSED, "seed_demo_quiz", unique=True)
        award_points(learner, 100, PointsTransaction.Reason.COURSE_COMPLETED, "seed_demo_course", unique=True)
        sync_user_xp(learner)

    def _content(self, author):
        faqs = [
            ("Accounts", "How do I create an account?", "Use your email address, choose a role, and set a strong password."),
            ("Courses", "Can I learn for free?", "Yes. Acadeval supports free courses and paid premium courses."),
            ("Certificates", "How are certificates verified?", "Each certificate has a unique ID and public verification page."),
            ("Payments", "Which payment methods are available?", "The demo includes card, mobile money, Paystack, and Flutterwave-ready payment records."),
            ("Organizations", "Can teams enroll learners in bulk?", "Yes. Organization accounts can bulk add learners, bulk enroll them, and export training reports."),
            ("Content", "Can admins add code, screenshots, tables, and outputs?", "Yes. Blog posts and lessons support rich ordered content blocks from the admin."),
        ]
        for index, (category, question, answer) in enumerate(faqs, start=1):
            FAQ.objects.update_or_create(question=question, defaults={"answer": answer, "category": category, "order": index, "is_active": True})

        posts = [
            ("How to Choose Your First Online Course", "A practical guide to choosing a course that matches your skill level and career goal."),
            ("Why Verified Certificates Matter", "Verified certificates help learners prove completion and help employers confirm authenticity."),
            ("How Teams Can Use Acadeval for Training", "Use bulk learners, bulk enrollment, and reports to run practical organization training."),
            ("A Beginner Guide to Learning With Code Blocks", "Use examples, outputs, tables, screenshots, and notes to learn technical topics faster."),
            ("From Lesson Notes to Portfolio Proof", "Turn each completed lesson into a small artifact that proves your practical progress."),
        ]
        for index, (title, excerpt) in enumerate(posts, start=1):
            post, _ = BlogPost.objects.update_or_create(
                title=title,
                defaults={"excerpt": excerpt, "content": "", "author": author, "is_published": True, "published_at": timezone.now()},
            )
            self._blog_blocks(post, index)

    def _blog_blocks(self, post, index):
        post.blocks.all().delete()
        rows = "Feature|Where it appears|Admin control\nCode fence|Blogs and lessons|Yes\nOutput|Blogs and lessons|Yes\nTables|Blogs and lessons|Yes"
        blocks = [
            (1, BlogContentBlock.BlockType.SUBTITLE, "Start with the outcome", "", ""),
            (2, BlogContentBlock.BlockType.SECTION, "Practical learning flow", "Read, practice, submit, and reflect", "Acadeval content is designed around small practical artifacts: code, outputs, screenshots, tables, notes, and assessments."),
            (3, BlogContentBlock.BlockType.CODE, "", "python", "steps = ['read', 'practice', 'submit']\nfor step in steps:\n    print(step)"),
            (4, BlogContentBlock.BlockType.OUTPUT, "Output", "", "read\npractice\nsubmit"),
            (5, BlogContentBlock.BlockType.TABLE, "Feature map", "", rows),
            (6, BlogContentBlock.BlockType.TILE, "Admin-ready content", "Reusable blocks", "Admins can compose posts and lessons with ordered blocks instead of editing one long text field."),
            (7, BlogContentBlock.BlockType.CALLOUT, "Try it", "", "Open the admin, edit this blog post, and rearrange or add blocks."),
        ]
        for order, block_type, title, subtitle, body in blocks:
            BlogContentBlock.objects.create(
                post=post,
                order=order,
                block_type=block_type,
                title=title,
                subtitle=subtitle if block_type != BlogContentBlock.BlockType.CODE else "",
                body=body,
                code_language="python" if block_type == BlogContentBlock.BlockType.CODE else "",
                table_data=body if block_type == BlogContentBlock.BlockType.TABLE else "",
            )