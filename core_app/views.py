from itertools import groupby
from collections import defaultdict
import datetime

from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, HttpResponseForbidden
from django.forms.models import model_to_dict


from rest_framework import viewsets
from rest_framework.response import Response
from rest_framework.decorators import api_view

from core_app.forms import (
    PageForm,
    RevisionEntryForm,
    StudentForm,
)
from core_app.models import PageRevision, Student
import src.quran_srs as qrs


from core_app.serializers import StudentSerializer


class StudentViewSet(viewsets.ModelViewSet):

    queryset = Student.objects.all()
    serializer_class = StudentSerializer

    def get_queryset(self):
        return super().get_queryset().filter(account=self.request.user)


def get_last_student(request):
    last_student = request.session.get("last_student")
    if last_student is None:
        last_student = request.user.student_set.all().first()
        last_student = model_to_dict(last_student)
        request.session["last_student"] = last_student
    return last_student


# this is an end point
@login_required
def home(request):
    return redirect("page_due", student_id=get_last_student(request)["id"])


@api_view(["GET", "PUT"])
def last_student(request):
    if request.method == "PUT":
        return Response({"message": "Got some data!", "data": request.data})
    else:
        return Response(get_last_student(request))


def page_summary(request):
    form = PageForm(request.POST or None)
    pages_list = request.session.get("pages", [])

    if form.is_valid():
        context = dict(request.POST.items())
        pages_list.append(context)
        request.session["pages"] = pages_list
    return render(request, "summary.html", {"pages_list": pages_list, "form": form})


def page_revision(request):
    revisions = PageRevision.objects.all()
    return render(request, "revisions.html", {"revisions": revisions})


def extract_record(revision):
    return (
        revision["date"],
        revision["word_mistakes"],
        revision["line_mistakes"],
        revision["current_interval"],
    )


keys_map = {
    "7.scheduled_interval": "Interval",
    "1.revision_number": "Revision Count",
    "mistakes": "Mistakes",
    "3.score": "Mistake Score",
    "page_strength": "Page Strength",
    "2.revision date": "Last Touch",
    "days_due": "Days Due",
    # "8.scheduled_due_date": "Due On",
}


def get_pages_due(student_id):
    revisions = (
        PageRevision.objects.filter(student=student_id).order_by("page").values()
    )
    revisions = groupby(revisions, lambda rev: rev["page"])
    pages_all = qrs.process_revision_data(revisions, extract_record)
    pages_due = {
        page: page_summary
        for page, page_summary in pages_all.items()
        if page_summary["is_due"]
    }
    return dict(pages_due)


@login_required
def page_due(request, student_id):
    student = Student.objects.get(id=student_id)
    if request.user != student.account:
        return HttpResponseForbidden(
            f"{student.name} is not a student of {request.user.username}"
        )

    request.session["last_student"] = model_to_dict(student)

    pages_due = get_pages_due(student_id)
    # Cache this so that revision entry page can automatically move to the next due page
    request.session["pages_due"] = pages_due
    return render(
        request,
        "due.html",
        {
            "pages_due": pages_due,
            "student": student,
            "keys_map": keys_map,
            "next_new_page": request.session.get("next_new_page"),
        },
    )


def page_new(request, student_id):
    return redirect("page_entry", student_id=student_id, page=request.GET.get("page"))


@login_required
def page_entry(request, student_id, page):
    student = Student.objects.get(id=student_id)
    if request.user != student.account:
        return HttpResponseForbidden(
            f"{student.name} is not a student of {request.user.username}"
        )

    revision_list = (
        PageRevision.objects.filter(student=student_id, page=page)
        .order_by("date")
        .values()
    )
    if revision_list:
        page_summary = qrs.process_page(page, revision_list, extract_record)
        new_page = False
    else:
        page_summary = {}
        new_page = True

    form = RevisionEntryForm(
        # request.POST or None, initial={"word_mistakes": 0, "line_mistakes": 0}
        request.POST or None,
        initial={},  # Removed initial default values
    )
    # interval_form = None

    if form.is_valid():
        word_mistakes = form.cleaned_data["word_mistakes"]
        line_mistakes = form.cleaned_data["line_mistakes"]

        PageRevision(
            student=student,
            page=page,
            word_mistakes=word_mistakes if word_mistakes else 0,
            line_mistakes=line_mistakes if line_mistakes else 0,
            # current_interval=interval_form.cleaned_data["next_interval"],
        ).save()

        if new_page:
            next_page = page + 1
            request.session["next_new_page"] = next_page
        else:
            pages_due = request.session.get("pages_due")
            pages_due.pop(str(page), None)
            request.session["pages_due"] = pages_due

            next_page = int(sorted(pages_due.keys(), key=int)[0])
        # return redirect("page_due", student_id=student.id)
        return redirect("page_entry", student_id=student.id, page=next_page)

    return render(
        request,
        "page_entry.html",
        {
            "page": page,
            "page_summary": page_summary,
            "form": form,
            # "interval_form": interval_form,
            "student_id": student_id,
            "keys_map": keys_map,
            "new_page": new_page,
        },
    )
