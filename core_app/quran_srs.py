import datetime
from itertools import groupby

from .models import PageRevision


def calculate_stats_for_all_pages(student_id):
    revisions = PageRevision.objects.filter(student=student_id)

    # groupby needs the revisions list to be sorted. Here we are sorting by page as we want to group by page
    revision_list_by_page = groupby(revisions.order_by("page"), lambda rev: rev.page)
    return {page: process_page(revision_list, student_id) for page, revision_list in revision_list_by_page}


def process_page(revision_list, student_id):
    last_revision = None
    page_summary = None
    for index, revision in enumerate(revision_list):
        revision.number = index + 1
        # Since revision_date was a datetime object, it was causing a subtle bug
        # in determining revision timings. Even on the due date,
        # it is flagging some revisions as EARLY based on the timestamp
        revision.date = revision.date.date()

        revision.score = get_page_score(revision)

        revision.interval_delta = get_interval_delta(revision)

        # This is first revision - Hence, the page can be new or can have a current interval
        # Take the current interval in the input data or make it zero
        if index == 0:
            update_current_interval_hack(revision, student_id)
            revision.score_cumulative = revision.score
        else:
            # We have the summary data from earlier revisions, hence we have to take use them
            revision.score_cumulative = page_summary.get("score_cumulative") + revision.score

            account_for_early_or_late_revision(revision, last_revision)

        set_max_interval(revision)
        set_next_interval(revision)
        set_due_date(revision)

        revision.page_strength = round(revision.next_interval / (index + 1), 1)  # Interval per revision
        revision.is_due = revision.due_date <= datetime.date.today()
        revision.overdue_days = (revision.due_date - datetime.date.today()).days  # TODO update today logic
        revision.mistakes_text = get_mistakes_text(revision)
        last_revision = revision

        page_summary = get_page_summary_dict(index, revision)

    return convert_datetime_to_str(page_summary)


def account_for_early_or_late_revision(revision, last_revision):
    scheduled_due_date = last_revision.due_date
    # ideally the page should be revised on the due date, not before or after
    if scheduled_due_date == revision.date:
        revision.timing = "ON_TIME_REVISION"
    elif scheduled_due_date < revision.date:
        revision.timing = "LATE_REVISION"
    else:
        revision.timing = "EARLY_REVISION"

    # By default, we take the scheduled interval from the last revision.
    # And then we will adjust it if the revision is late or early
    revision.current_interval = last_revision.next_interval

    # For Late Revisions
    # Increase interval by the extra days if the score has improved since last time.
    # Otherwise use the last interval - No need to do anything as it is already set above
    if revision.timing == "LATE_REVISION" and score_improved(revision, last_revision):
        revision.interval_delta += revision_delay(revision, last_revision)  # NEW

    # For Early Revisions
    # If more than 1 line mistake and the score has fallen since last time,
    # decrease the interval by the left-over days
    # Otherwise just add 1 as interval delta to increase interval due to unscheduled revision
    if revision.timing == "EARLY_REVISION":
        if revision.line_mistakes > 1 and not score_improved(revision, last_revision):
            revision.interval_delta += revision_delay(revision, last_revision)

        else:
            revision.interval_delta = 1


def set_due_date(revision):
    # If the interval is negative or zero, we want to revise the next day
    day_offset = 1 if revision.next_interval <= 0 else revision.next_interval
    revision.due_date = revision.date + datetime.timedelta(days=day_offset)


def convert_datetime_to_str(page_summary):
    # Since this dict will be stored in session,
    # we need to convert datetime objects into a string representation
    return {
        key: value.strftime("%Y-%m-%d") if isinstance(value, datetime.date) else value
        for key, value in page_summary.items()
    }


def get_page_summary_dict(index, revision):
    return {
        "1.revision_number": revision.number,
        "2.revision date": revision.date,
        "3.score": revision.score,
        "4.current_interval": revision.current_interval,
        "5.interval_delta": revision.interval_delta,
        "6.max_interval": revision.max_interval,
        "7.scheduled_interval": revision.next_interval,
        "8.scheduled_due_date": revision.due_date,
        "page_strength": revision.page_strength,
        "is_due": revision.is_due,
        "overdue_days": revision.overdue_days,
        "mistakes": revision.mistakes_text,
        "score_cumulative": revision.score_cumulative,
        "score_average": round(revision.score_cumulative / (index + 1), 2),
    }


def revision_delay(revision, last_revision):
    return (revision.date - last_revision.due_date).days


def score_improved(revision, last_revision):
    return 60 - revision.score >= 60 - last_revision.score


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


def update_current_interval_hack(revision, student_id):
    # Temp hack to reduce too-many due pages for Safwan and Hanan
    if student_id == 3:
        revision.interval_delta += 10 if revision.score == 0 else 5
    elif student_id == 4:
        revision.interval_delta += 15 if revision.score == 0 else 7


def get_mistakes_text(revision):
    # More readable mistakes string
    mistakes_text = "-"
    if revision.line_mistakes != 0:
        mistakes_text = str(revision.line_mistakes) + "L "

    if revision.word_mistakes != 0:
        if revision.line_mistakes != 0:
            mistakes_text += str(revision.word_mistakes) + "W"
        else:
            mistakes_text = str(revision.word_mistakes) + "W"
    return mistakes_text
