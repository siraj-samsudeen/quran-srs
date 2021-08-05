from collections import Counter

from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404

from . import quran_srs as qrs
from .models import Student


def get_pages_due(student_id):
    pages_all = qrs.calculate_stats_for_all_pages(student_id)
    pages_due = [page_summary for page_summary in pages_all if page_summary["is_due"]]

    counter = Counter()
    for page_summary in pages_all:
        counter.update({page_summary["due_date"]: 1})

    counter = dict(sorted(counter.items()))

    return pages_due, counter, len(pages_all)


def check_access_rights_and_get_student(request, student_id):
    student = get_object_or_404(Student, id=student_id)
    if request.user != student.account:
        raise PermissionDenied(f"{student.name} is not a student of {request.user.username}")
    return student
