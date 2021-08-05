import datetime
from itertools import groupby

from .models import PageRevision


def calculate_stats_for_all_pages(student_id):
    revisions = PageRevision.objects.filter(student=student_id)

    # groupby needs the revisions list to be sorted. Here we are sorting by page as we want to group by page
    revision_list_by_page = groupby(revisions.order_by("page"), lambda rev: rev.page)
    return [
        {"page": page, **calculate_stats_for_page(revision_list, student_id)}
        for page, revision_list in revision_list_by_page
    ]


def calculate_stats_for_page(revision_list, student_id):
    last_revision = None
    page_summary = None
    for index, revision in enumerate(revision_list):
        revision.number = index + 1
        # Since revision_date was a datetime object, it was causing a subtle bug
        # in determining revision timings. Even on the due date,
        # it is flagging some revisions as EARLY based on the timestamp
        revision.date_trunc = revision.date.date()

        revision.score = get_page_score(revision)
        revision.interval_delta = get_interval_delta(revision)

        if index == 0:
            increase_starting_interval_for_some_students(revision, student_id)
        else:
            # By default, we take the scheduled interval from the last revision.
            # And then we will adjust it if the revision is late or early
            revision.current_interval = last_revision.next_interval
            account_for_early_or_late_revision(revision, last_revision)

        set_max_interval(revision)
        set_next_interval(revision)
        set_due_date(revision)

        last_revision = revision

        page_summary = get_page_summary_dict(revision)

    return page_summary


# TODO change score to a negative
def get_page_score(revision):
    # each page has 15 lines - each line is worth 4 points. So, max point is 15*4 = 60
    # Each word mistake takes away 1 point, and each line mistake 4 points.
    # If the total page is gone, the score would be zero.
    # return 60 - word_mistakes * 1 - line_mistakes * 4
    return revision.word_mistakes * 1 + revision.line_mistakes * 4


def get_interval_delta(revision):
    # Convert score into an interval delta
    if revision.score == 0:  # Perfect page
        return +3
    elif revision.score == 1:  # 1 Word Mistake
        return +2
    elif revision.score <= 3:  # 3 Word Mistakes
        return +1
    elif revision.score == 4:  # 1 Line Mistake
        return 0
    elif revision.score <= 8:  # 2 Line Mistakes
        return -1
    elif revision.score <= 12:  # 3 Line Mistakes
        return -2
    elif revision.score <= 20:  # 5 Line Mistakes
        return -3
    elif revision.score <= 30:  # 7.5 Line Mistakes - Half a page
        return -5
    else:  # More than half a page
        return -7


def increase_starting_interval_for_some_students(revision, student_id):
    # Temp hack to reduce too-many due pages for Safwan and Hanan
    if student_id == 3:
        revision.interval_delta += 10 if revision.score == 0 else 5
    elif student_id == 4:
        revision.interval_delta += 15 if revision.score == 0 else 7


def account_for_early_or_late_revision(revision, last_revision):
    revision_delay = (revision.date_trunc - last_revision.due_date).days

    # For Late Revisions
    # Increase interval by the extra days if the score has improved since last time.
    # Otherwise use the last interval - No need to do anything as it is already set above
    if revision_delay > 0 and score_improved(revision, last_revision):
        revision.interval_delta += revision_delay

    # For Early Revisions
    # If more than 1 line mistake and the score has fallen since last time,
    # decrease the interval by the left-over days
    # Otherwise just add 1 as interval delta to increase interval due to unscheduled revision
    if revision_delay < 0:
        if revision.line_mistakes > 1 and not score_improved(revision, last_revision):
            revision.interval_delta += revision_delay

        else:
            revision.interval_delta = 1


def score_improved(revision, last_revision):
    return 60 - revision.score >= 60 - last_revision.score


def set_max_interval(revision):

    # If Score is 8 or more (2 line mistakes or more), then we have to restrict the max Interval
    if revision.score < 4:
        revision.max_interval = None
    elif revision.score == 4:  # 1 Line Mistake - 40 days max
        revision.max_interval = 40
    elif revision.score <= 8:  # 2 Line Mistakes - 30 days/1 month max
        revision.max_interval = 30
    elif revision.score <= 12:  # 3 Line Mistakes - 3 weeks max
        revision.max_interval = 21
    elif revision.score <= 20:  # 5 Line Mistakes - 2 weeks max
        revision.max_interval = 14
    elif revision.score <= 30:  # 7.5 Line Mistakes - Half a page - 1 week max
        revision.max_interval = 7
    else:  # More than half a page - 3 days max
        revision.max_interval = 3


def set_next_interval(revision):
    next_interval = revision.current_interval + revision.interval_delta  # NEW

    if revision.difficulty_level == "e":
        if next_interval <= 15:
            revision.interval_delta += 5
        elif next_interval <= 30:
            revision.interval_delta += 3
        else:
            revision.interval_delta += 1

    elif revision.difficulty_level == "h":
        if next_interval >= 20:
            revision.interval_delta -= 5
        elif next_interval >= 10:
            revision.interval_delta -= 3
        elif next_interval >= 3:
            revision.interval_delta -= 1

    revision.next_interval = revision.current_interval + revision.interval_delta  # NEW

    # Restrict the next interval to max interval if is smaller
    if revision.max_interval and revision.max_interval < next_interval:
        revision.next_interval = revision.max_interval


def set_due_date(revision):
    # If the interval is negative or zero, we want to revise the next day
    day_offset = 1 if revision.next_interval <= 0 else revision.next_interval
    revision.due_date = revision.date_trunc + datetime.timedelta(days=day_offset)

    revision.is_due = revision.due_date <= datetime.date.today()
    revision.overdue_days = (revision.due_date - datetime.date.today()).days  # TODO update today logic


def get_page_summary_dict(revision):
    return {
        "interval": revision.next_interval,
        "Rev #": revision.number,
        "previous_interval": revision.current_interval,
        "last_revision": revision.date_trunc,
        "score": revision.score,
        "due_date": revision.due_date,
        "is_due": revision.is_due,
        "overdue_days": revision.overdue_days,
    }
