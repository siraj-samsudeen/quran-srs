from collections import Counter

from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404

from . import quran_srs as qrs
from .models import Student


def get_pages_due(student_id):
    pages_all = qrs.calculate_stats_for_all_pages(student_id)
    pages_due = {page: page_summary for page, page_summary in pages_all.items() if page_summary["is_due"]}

    counter = Counter()
    for _, page_summary in pages_all.items():
        counter.update({page_summary["scheduled_due_date"]: 1})

    counter = dict(sorted(counter.items()))

    return dict(pages_due), counter, len(pages_all)


def check_access_rights_and_get_student(request, student_id):
    student = get_object_or_404(Student, id=student_id)
    if request.user != student.account:
        raise PermissionDenied(f"{student.name} is not a student of {request.user.username}")
    return student
