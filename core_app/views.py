from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render

from . import quran_srs as qrs

from .forms import RevisionEntryForm
from .models import PageRevision

from . import utils


@login_required
def home(request):
    return render(request, "home.html", {"students": request.user.student_set.all()})


@login_required
def page_all(request, student_id):
    student = utils.check_access_rights_and_get_student(request, student_id)

    return render(
        request,
        "all.html",
        {
            "pages_all": qrs.calculate_stats_for_all_pages(student_id),
            "student": student,
        },
    )


@login_required
def page_due(request, student_id):
    student = utils.check_access_rights_and_get_student(request, student_id)

    pages_due, counter = utils.get_pages_due(student_id)

    # Cache this so that revision entry page can automatically move to the next due page
    next_page_key = "next_new_page" + str(student_id)

    return render(
        request,
        "due.html",
        {
            "pages_due": pages_due,
            "student": student,
            "next_new_page": request.session.get(next_page_key),
            "due_date_summary": counter,
        },
    )


@login_required
def page_entry(request, student_id, page, due_page):
    student = utils.check_access_rights_and_get_student(request, student_id)

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
            word_mistakes=word_mistakes or 0,
            line_mistakes=line_mistakes or 0,
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
            "form": form,
            "student": student,
            "new_page": new_page,
        },
    )


def page_new(request, student_id):
    return redirect("page_entry", student_id=student_id, page=request.GET.get("page"), due_page=0)
