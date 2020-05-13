from django.test import TestCase
import src.quran_srs as srs
from core_app.models import Student, PageRevision
from django.contrib.auth.models import User
from core_app.views import extract_record

# Create your tests here.


STUDENT_ID = 1


class SRSTestCase(TestCase):
    def setUp(self):
        # store the password to login later
        password = "mypassword"

        my_admin = User.objects.create_superuser("myuser", "myemail@test.com", password)
        Student.objects.create(account=my_admin)

    def test_perfect_page(self):
        student = Student.objects.get(id=STUDENT_ID)
        self.assertEqual(student.id, STUDENT_ID)

        page = 2

        revision_date = "2020-04-11"
        PageRevision(
            student=student,
            page=page,
            word_mistakes=0,
            line_mistakes=0,
            difficulty_level="o",
            date=revision_date,
        ).save()
        revision_list = (
            PageRevision.objects.filter(student=STUDENT_ID, page=page)
            .order_by("date")
            .values()
        )
        page_summary = srs.process_page(page, revision_list, extract_record, STUDENT_ID)
        self.assertEqual(page_summary["7.scheduled_interval"], 3)

        revision_date = "2020-04-14"
        PageRevision(student=student, page=page, date=revision_date,).save()
        revision_list = (
            PageRevision.objects.filter(student=STUDENT_ID, page=page)
            .order_by("date")
            .values()
        )
        page_summary = srs.process_page(page, revision_list, extract_record, STUDENT_ID)
        self.assertEqual(page_summary["7.scheduled_interval"], 6)

        # Early revision
        revision_date = "2020-04-15"
        PageRevision(student=student, page=page, date=revision_date,).save()
        revision_list = (
            PageRevision.objects.filter(student=STUDENT_ID, page=page)
            .order_by("date")
            .values()
        )
        page_summary = srs.process_page(page, revision_list, extract_record, STUDENT_ID)
        self.assertEqual(page_summary["7.scheduled_interval"], 6 + 1)

        # Late revision
        revision_date = "2020-04-22"
        PageRevision(student=student, page=page, date=revision_date,).save()
        revision_list = (
            PageRevision.objects.filter(student=STUDENT_ID, page=page)
            .order_by("date")
            .values()
        )
        page_summary = srs.process_page(page, revision_list, extract_record, STUDENT_ID)
        self.assertEqual(page_summary["7.scheduled_interval"], 7 + 3)

    def test_page_23(self):
        student = Student.objects.get(id=STUDENT_ID)
        page = 23

        revision_date = "2020-01-22"
        PageRevision(
            student=student,
            page=page,
            word_mistakes=0,
            line_mistakes=0,
            difficulty_level="o",
            date=revision_date,
        ).save()
        revision_list = (
            PageRevision.objects.filter(student=STUDENT_ID, page=page)
            .order_by("date")
            .values()
        )
        page_summary = srs.process_page(page, revision_list, extract_record, STUDENT_ID)
        self.assertEqual(page_summary["7.scheduled_interval"], 3)

        revision_date = "2020-01-26"
        PageRevision(
            student=student, page=page, word_mistakes=1, date=revision_date,
        ).save()
        revision_list = (
            PageRevision.objects.filter(student=STUDENT_ID, page=page)
            .order_by("date")
            .values()
        )
        page_summary = srs.process_page(page, revision_list, extract_record, STUDENT_ID)
        self.assertEqual(page_summary["7.scheduled_interval"], 5)

        revision_date = "2020-01-31"
        PageRevision(student=student, page=page, date=revision_date,).save()
        revision_list = (
            PageRevision.objects.filter(student=STUDENT_ID, page=page)
            .order_by("date")
            .values()
        )
        page_summary = srs.process_page(page, revision_list, extract_record, STUDENT_ID)
        self.assertEqual(page_summary["7.scheduled_interval"], 8)

        revision_date = "2020-02-09"
        PageRevision(
            student=student, page=page, word_mistakes=1, date=revision_date,
        ).save()
        revision_list = (
            PageRevision.objects.filter(student=STUDENT_ID, page=page)
            .order_by("date")
            .values()
        )
        page_summary = srs.process_page(page, revision_list, extract_record, STUDENT_ID)
        self.assertEqual(page_summary["7.scheduled_interval"], 10)

        revision_date = "2020-02-19"
        PageRevision(student=student, page=page, date=revision_date,).save()
        revision_list = (
            PageRevision.objects.filter(student=STUDENT_ID, page=page)
            .order_by("date")
            .values()
        )
        page_summary = srs.process_page(page, revision_list, extract_record, STUDENT_ID)
        self.assertEqual(page_summary["7.scheduled_interval"], 13)

        revision_date = "2020-03-01"
        PageRevision(student=student, page=page, date=revision_date,).save()
        revision_list = (
            PageRevision.objects.filter(student=STUDENT_ID, page=page)
            .order_by("date")
            .values()
        )
        page_summary = srs.process_page(page, revision_list, extract_record, STUDENT_ID)
        self.assertEqual(page_summary["7.scheduled_interval"], 13 + 1)

        revision_date = "2020-03-14"
        PageRevision(student=student, page=page, date=revision_date,).save()
        revision_list = (
            PageRevision.objects.filter(student=STUDENT_ID, page=page)
            .order_by("date")
            .values()
        )
        page_summary = srs.process_page(page, revision_list, extract_record, STUDENT_ID)
        self.assertEqual(page_summary["7.scheduled_interval"], 14 + 1)
