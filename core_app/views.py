import datetime
import math
from collections import Counter

import numpy as np
import pandas as pd
from django.contrib.auth.decorators import login_required
from django.forms.models import model_to_dict
from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render
from rest_framework import viewsets
from rest_framework.decorators import api_view
from rest_framework.response import Response

import core_app.quran_srs as qrs
from core_app.forms import RevisionEntryForm
from core_app.models import PageRevision, Student
from core_app.serializers import StudentSerializer


class StudentViewSet(viewsets.ModelViewSet):

    queryset = Student.objects.all()
    serializer_class = StudentSerializer

    def get_queryset(self):
        return super().get_queryset().filter(account=self.request.user)


def get_last_student(request):
    last_student_local = request.session.get("last_student")
    if last_student_local is None:
        last_student_local = request.user.student_set.all().first()
        last_student_local = model_to_dict(last_student_local)
        request.session["last_student"] = last_student_local
    return last_student_local


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
        return HttpResponseForbidden(f"{student.name} is not a student of {request.user.username}")

    request.session["last_student"] = model_to_dict(student)
    next_page_key = "next_new_page" + str(student_id)

    return render(
        request,
        "all.html",
        {
            "pages_all": dict(qrs.calculate_stats_for_all_pages(student_id)),
            "student": student,
            "keys_map": keys_map_all,
            "next_new_page": request.session.get(next_page_key),
        },
    )


keys_map = {
    "7.scheduled_interval": "Int",
    "1.revision_number": "Rev",
    "overdue_days": "Due in",
    "page_strength": "Int/Rev",
    "3.score": "Last Score",
    "sort_order": "Sort Order",
    "risk_rank": "Risk Rank",
    "8.scheduled_due_date": "Due",
    "2.revision date": "LastTouch",
}

keys_map_all = {key: value for key, value in keys_map.items() if key not in ["sort_order", "risk_rank"]}

keys_map_due = {
    key: value
    for key, value in keys_map.items()
    if key
    not in [
        "2.revision date",
        "8.scheduled_due_date",
    ]
}

keys_map_revision_entry = {
    key: value
    for key, value in keys_map.items()
    if key
    in [
        "7.scheduled_interval",
        "1.revision_number",
        "overdue_days",
    ]
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

    request.session["last_student"] = model_to_dict(student)

    pages_due, counter, total_page_count = get_pages_due(student_id)

    if pages_due:
        # Implement the algorithm to computer page risk

        df = pd.DataFrame.from_dict(
            pages_due,
            orient="index",
        )
        df.drop(
            [
                "2.revision date",
                "8.scheduled_due_date",
                "4.current_interval",
                "5.interval_delta",
                "6.max_interval",
                "is_due",
            ],
            axis=1,
            inplace=True,
        )

        df.rename(
            columns={
                "7.scheduled_interval": "interval",
                "1.revision_number": "revisions",
                "3.score": "latest_score",
                "page_strength": "interval_per_revision",
                "overdue_days": "overdue_days",
            },
            inplace=True,
        )

        cols_new_order = [
            "interval",
            "revisions",
            "latest_score",
            "interval_per_revision",
            "overdue_days",
        ]
        df = df[cols_new_order]

        df["interval_modified"] = np.where(df.interval >= 30, -1 * df.interval, df.interval)
        df["rank_interval"] = df["interval_modified"].rank(pct=True, ascending=False)
        df["rank_revisions"] = df["revisions"].rank(pct=True, ascending=False)
        df["rank_latest_score"] = df["latest_score"].rank(pct=True, ascending=True)
        df["rank_interval_per_revision"] = df["interval_per_revision"].rank(pct=True, ascending=False)
        df["rank_overdue_days"] = df["overdue_days"].rank(pct=True, ascending=False)
        df["rank_overall"] = (
            df.rank_interval
            + df.rank_revisions
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
            page_bin = math.ceil(risk_rank / 10)
            # Now order the pages based on page number within each bin; page = index in the data frame
            sort_order = round(page_bin + (index / 1000), 3)
            pages_due[index].update({"sort_order": sort_order})

        # Cache this so that revision entry page can automatically move to the next due page
    request.session["pages_due"] = pages_due
    next_page_key = "next_new_page" + str(student_id)

    return render(
        request,
        "due.html",
        {
            "pages_due": pages_due,
            "student": student,
            "keys_map": keys_map_due,
            "next_new_page": request.session.get(next_page_key),
            "due_date_summary": counter,
            "total_page_count": total_page_count,
        },
    )


def page_new(request, student_id):
    return redirect("page_entry", student_id=student_id, page=request.GET.get("page"), due_page=0)


def page_revision(request, student_id, page):
    student = Student.objects.get(id=student_id)
    if request.user != student.account:
        return HttpResponseForbidden(f"{student.name} is not a student of {request.user.username}")

    revision_list = PageRevision.objects.filter(student=student_id, page=page).order_by("date").values()

    # revisions = PageRevision.objects.all()
    return render(
        request,
        "revisions.html",
        {"revision_list": revision_list, "student": student, "page": page},
    )


@login_required
def page_revise(request, student_id):
    student = Student.objects.get(id=student_id)

    # Filter to show only the pages revised in the last 24 hours
    last_24_hours = datetime.date.today() - datetime.timedelta(hours=24)
    revision_list = (
        PageRevision.objects.filter(
            student=student_id,
            date__gte=last_24_hours,
            # line_mistakes__gte=1
        )
        .order_by("date")
        .values()
    )

    rev_list = []
    for rev in revision_list:
        score = rev["word_mistakes"] + rev["line_mistakes"] * 4
        rev["score"] = score
        rev_list.append(rev)

    return render(
        request,
        "pages_to_revise.html",
        {"revision_list": rev_list, "student": student},
    )


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
            pages_due = request.session.get("pages_due")
            pages_due.pop(str(page), None)
            request.session["pages_due"] = pages_due

            # if there are no more due pages, redirect to the main page.
            if pages_due:
                pages_due_sorted = sorted(
                    pages_due.items(),
                    key=lambda key_value: key_value[1]["sort_order"],
                )
                next_page = int(pages_due_sorted[0][0])

                return redirect("page_entry", student_id=student.id, page=next_page, due_page=1)
            else:
                return redirect("page_due", student_id=student.id)

    pages_due = request.session.get("pages_due")

    next_page_set = []
    if pages_due:
        pages_due_sorted = sorted(
            pages_due.items(),
            key=lambda key_value: key_value[1]["sort_order"],
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
