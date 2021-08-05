import datetime
from collections import Counter

from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404

from . import quran_srs as qrs
from .models import Student


def get_pages_due(student_id):
    pages_all = qrs.calculate_stats_for_all_pages(student_id)

    pages_due = [page_summary for page_summary in pages_all if page_summary["due_date"] <= datetime.date.today()]

    counter = get_due_page_summary_till_next_week(pages_all)

    return pages_due, counter


def get_due_page_summary_till_next_week(pages_all):
    counter = Counter()
    today = datetime.date.today()

    for page_summary in pages_all:
        due_date = page_summary["due_date"]
        if due_date > today + datetime.timedelta(days=7):  # We want a max of one week from now
            continue
        due_date = max(due_date, today)  # Put all the past dates into today
        counter.update({due_date: 1})

    counter = dict(sorted(counter.items()))
    return counter


def check_access_rights_and_get_student(request, student_id):
    student = get_object_or_404(Student, id=student_id)
    if request.user != student.account:
        raise PermissionDenied(f"{student.name} is not a student of {request.user.username}")
    return student
