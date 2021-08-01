from collections import Counter

from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render

import core_app.quran_srs as qrs
from core_app.forms import RevisionEntryForm
from core_app.models import PageRevision, Student


@login_required
def home(request):
    return render(request, "home.html", {"students": request.user.student_set.all()})


def page_all(request, student_id):
    student = Student.objects.get(id=student_id)
    if request.user != student.account:
        return HttpResponseForbidden(f"{student.name} is not a student of {request.user.username}")

    next_page_key = "next_new_page" + str(student_id)

    return render(
        request,
        "all.html",
        {
            "pages_all": dict(qrs.calculate_stats_for_all_pages(student_id)),
            "student": student,
            "keys_map": keys_map,
            "next_new_page": request.session.get(next_page_key),
        },
    )


keys_map = {
    "7.scheduled_interval": "Int",
    "1.revision_number": "Rev",
    "overdue_days": "Due in",
    "page_strength": "Int/Rev",
    "3.score": "Last Score",
    "8.scheduled_due_date": "Due",
    "2.revision date": "LastTouch",
}


def get_pages_due(student_id):
    pages_all = qrs.calculate_stats_for_all_pages(student_id)
    pages_due = {page: page_summary for page, page_summary in pages_all.items() if page_summary["is_due"]}

    counter = Counter()
    for _, page_summary in pages_all.items():
        counter.update({page_summary["8.scheduled_due_date"]: 1})

    counter = dict(sorted(counter.items()))

    return dict(pages_due), counter, len(pages_all)


@login_required
def page_due(request, student_id):
    # student = Student.objects.get(id=student_id)
    student = get_object_or_404(Student, id=student_id)
    if request.user != student.account:
        return HttpResponseForbidden(f"{student.name} is not a student of {request.user.username}")

    pages_due, counter, total_page_count = get_pages_due(student_id)

    # Cache this so that revision entry page can automatically move to the next due page
    next_page_key = "next_new_page" + str(student_id)

    return render(
        request,
        "due.html",
        {
            "pages_due": pages_due,
            "student": student,
            "keys_map": keys_map,
            "next_new_page": request.session.get(next_page_key),
            "due_date_summary": counter,
            "total_page_count": total_page_count,
        },
    )


def page_new(request, student_id):
    return redirect("page_entry", student_id=student_id, page=request.GET.get("page"), due_page=0)


@login_required
def page_entry(request, student_id, page, due_page):
    student = Student.objects.get(id=student_id)
    if request.user != student.account:
        return HttpResponseForbidden(f"{student.name} is not a student of {request.user.username}")

    revision_list = PageRevision.objects.filter(student=student_id, page=page).order_by("date")
    if revision_list:
        page_summary = qrs.calculate_stats_for_page(revision_list, student_id)
        new_page = False
    else:
        page_summary = {}
        new_page = True

    form = RevisionEntryForm(
        # request.POST or None, initial={"word_mistakes": 0, "line_mistakes": 0}
        request.POST
        or None
    )

    if form.is_valid():
        word_mistakes = form.cleaned_data["word_mistakes"]
        line_mistakes = form.cleaned_data["line_mistakes"]
        difficulty_level = form.cleaned_data["difficulty_level"]

        PageRevision(
            student=student,
            page=page,
            word_mistakes=word_mistakes if word_mistakes else 0,
            line_mistakes=line_mistakes if line_mistakes else 0,
            difficulty_level=difficulty_level,
        ).save()

        if due_page == 0:
            next_page = page + 1
            next_page_key = "next_new_page" + str(student_id)
            request.session[next_page_key] = next_page
            return redirect("page_entry", student_id=student.id, page=next_page, due_page=0)
        else:
            return redirect("page_due", student_id=student.id)

    return render(
        request,
        "page_entry.html",
        {
            "page": page,
            "page_summary": page_summary,
            "revision_list": revision_list,
            "form": form,
            "student": student,
            "keys_map": keys_map,
            "new_page": new_page,
            "due_page": due_page,
        },
    )
