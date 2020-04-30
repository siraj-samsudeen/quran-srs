from itertools import groupby
from collections import defaultdict
import datetime
import math

from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, HttpResponseForbidden
from django.forms.models import model_to_dict


from rest_framework import viewsets
from rest_framework.response import Response
from rest_framework.decorators import api_view

import pandas as pd
import numpy as np

from core_app.forms import (
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


def page_all(request, student_id):
    student = Student.objects.get(id=student_id)
    if request.user != student.account:
        return HttpResponseForbidden(
            f"{student.name} is not a student of {request.user.username}"
        )

    request.session["last_student"] = model_to_dict(student)

    return render(
        request,
        "all.html",
        {
            "pages_all": dict(get_pages_all(student_id)),
            "student": student,
            "keys_map": keys_map_all,
            "next_new_page": request.session.get("next_new_page"),
        },
    )


def extract_record(revision):
    return (
        revision["date"],
        revision["word_mistakes"],
        revision["line_mistakes"],
        revision["current_interval"],
        revision["difficulty_level"],
    )


keys_map = {
    "7.scheduled_interval": "Interval",
    "1.revision_number": "Revisions",
    "mistakes": "Latest Mistakes",
    "3.score": "Latest Score",
    "score_average": "Average Score",
    "page_strength": "Interval / Revision",
    "2.revision date": "Last Touch",
    "8.scheduled_due_date": "Due On",
    "overdue_days": "Overdue Days",
    "risk_rank": "Risk Rank",
    "sort_order": "Sort Order",
}

keys_map_all = {
    key: value for key, value in keys_map.items() if key not in ["risk_rank",]
}

keys_map_due = {
    key: value
    for key, value in keys_map.items()
    if key in ["7.scheduled_interval", "1.revision_number", "mistakes", "sort_order",]
}

keys_map_revision_entry = {
    key: value
    for key, value in keys_map.items()
    if key
    in [
        "7.scheduled_interval",
        "2.revision date",
        "1.revision_number",
        "overdue_days",
        "mistakes",
    ]
}


def get_pages_all(student_id):
    revisions = (
        PageRevision.objects.filter(student=student_id).order_by("page").values()
    )
    revisions = groupby(revisions, lambda rev: rev["page"])
    return qrs.process_revision_data(revisions, extract_record, student_id)


def get_pages_due(student_id):
    pages_all = get_pages_all(student_id)
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

    if pages_due:
        # Implement the algorithm to computer page risk

        df = pd.DataFrame.from_dict(pages_due, orient="index",)
        df.drop(
            [
                "2.revision date",
                "8.scheduled_due_date",
                "mistakes",
                "4.current_interval",
                "5.interval_delta",
                "6.max_interval",
                "is_due",
                "score_cumulative",
            ],
            axis=1,
            inplace=True,
        )

        df.rename(
            columns={
                "7.scheduled_interval": "interval",
                "1.revision_number": "revisions",
                "score_average": "average_score",
                "3.score": "latest_score",
                "page_strength": "interval_per_revision",
                "overdue_days": "overdue_days",
            },
            inplace=True,
        )

        cols_new_order = [
            "interval",
            "revisions",
            "average_score",
            "latest_score",
            "interval_per_revision",
            "overdue_days",
        ]
        df = df[cols_new_order]

        df["interval_modified"] = np.where(
            df.interval >= 30, -1 * df.interval, df.interval
        )
        df["rank_interval"] = df["interval_modified"].rank(pct=True, ascending=False)
        df["rank_revisions"] = df["revisions"].rank(pct=True, ascending=False)
        df["rank_average_score"] = df["average_score"].rank(pct=True, ascending=True)
        df["rank_latest_score"] = df["latest_score"].rank(pct=True, ascending=True)
        df["rank_interval_per_revision"] = df["interval_per_revision"].rank(
            pct=True, ascending=False
        )
        df["rank_overdue_days"] = df["overdue_days"].rank(pct=True, ascending=False)
        df["rank_overall"] = (
            df.rank_interval
            + df.rank_revisions
            + df.rank_average_score
            + df.rank_latest_score
            + df.rank_interval_per_revision
            + df.rank_overdue_days
        )
        # Need a unique rank for each item even if there are ties
        df["risk_rank"] = df["rank_overall"].rank(ascending=False, method="first")

        for index, row in df.iterrows():
            risk_rank = row["risk_rank"]
            pages_due[index].update({"risk_rank": int(row["risk_rank"])})

            # Group pages into bins of 10 so that they can be tackled together
            bin = math.ceil(risk_rank / 10)
            # Now order the pages based on page number within each bin; page = index in the data frame
            sort_order = round(bin + (index / 1000), 3)
            pages_due[index].update({"sort_order": sort_order})

        # Cache this so that revision entry page can automatically move to the next due page
    request.session["pages_due"] = pages_due

    return render(
        request,
        "due.html",
        {
            "pages_due": pages_due,
            "student": student,
            "keys_map": keys_map_due,
            "next_new_page": request.session.get("next_new_page"),
        },
    )


def page_new(request, student_id):
    return redirect(
        "page_entry", student_id=student_id, page=request.GET.get("page"), due_page=0
    )


def page_revision(request, student_id, page):
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

    # revisions = PageRevision.objects.all()
    return render(
        request,
        "revisions.html",
        {"revision_list": revision_list, "student": student, "page": page},
    )


@login_required
def page_entry(request, student_id, page, due_page):
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
        page_summary = qrs.process_page(page, revision_list, extract_record, student_id)
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
            request.session["next_new_page"] = next_page
            return redirect(
                "page_entry", student_id=student.id, page=next_page, due_page=0
            )
        else:
            pages_due = request.session.get("pages_due")
            pages_due.pop(str(page), None)
            request.session["pages_due"] = pages_due

            # if there are no more due pages, redirect to the main page.
            if pages_due:
                pages_due_sorted = sorted(
                    pages_due.items(), key=lambda key_value: key_value[1]["sort_order"],
                )
                next_page = int(pages_due_sorted[0][0])

                return redirect(
                    "page_entry", student_id=student.id, page=next_page, due_page=1
                )
            else:
                return redirect("page_due", student_id=student.id)

    pages_due = request.session.get("pages_due")

    next_page_set = []
    if pages_due:
        pages_due_sorted = sorted(
            pages_due.items(), key=lambda key_value: key_value[1]["sort_order"],
        )

        for i in range(0, len(pages_due.keys())):
            next_page_set.append(int(pages_due_sorted[i][0]))


    return render(
        request,
        "page_entry.html",
        {
            "page": page,
            "page_summary": page_summary,
            "revision_list": revision_list,
            "form": form,
            "student": student,
            "keys_map": keys_map_revision_entry,
            "new_page": new_page,
            "next_page_set": next_page_set,
            "next_page_set_sorted": sorted(next_page_set),
            "due_page": due_page,
        },
    )
