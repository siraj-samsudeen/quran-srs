import datetime
from collections import defaultdict
from itertools import groupby

from core_app.models import PageRevision


def calculate_stats_for_all_pages(student_id):
    revisions = PageRevision.objects.filter(student=student_id)

    # groupby needs the revisions list to be sorted. Here we are sorting by page as we want to group by page
    revision_list_by_page = groupby(revisions.order_by("page"), lambda rev: rev.page)
    return {
        page: process_page(revision_list, student_id)
        for page, revision_list in revision_list_by_page
    }


def process_page(revision_list, student_id):
    page_summary = {}
    for index, revision in enumerate(revision_list):
        # Since revision_date was a datetime object, it was causing a subtle bug
        # in determining revision timings. Even on the due date,
        # it is flagging some revisions as EARLY based on the timestamp
        revision_date = revision.date.date()
        word_mistakes = revision.word_mistakes
        line_mistakes = revision.line_mistakes
        current_interval = revision.current_interval
        difficulty_level = revision.difficulty_level

        score = get_page_score(word_mistakes, line_mistakes)

        interval_delta = get_interval_delta(score)

        # This is first revision - Hence, the page can be new or can have a current interval
        # Take the current interval in the input data or make it zero
        if index == 0:
            current_interval = update_current_interval_hack(
                current_interval, student_id, score
            )
            score_cumulative = score
        else:
            # We have the summary data from earlier revisions, hence we have to take use them
            scheduled_interval = page_summary.get("7.scheduled_interval")
            scheduled_due_date = page_summary.get("8.scheduled_due_date")
            last_score = page_summary.get("3.score")
            score_cumulative = page_summary.get("score_cumulative") + score

            revision_timing = get_revision_timing(scheduled_due_date, revision_date)

            # By default, we take the scheduled interval from the last revision.
            # And then we will adjust it if the revision is late or early
            current_interval = scheduled_interval

            # For Late Revisions
            # Increase interval by the extra days if the score has improved since last time.
            # Otherwise use the last interval - No need to do anything as it is already set above
            if revision_timing == "LATE_REVISION" and 60 - score >= 60 - last_score:
                current_interval = (
                    scheduled_interval + (revision_date - scheduled_due_date).days
                )

            # For Early Revisions
            # If more than 1 line mistake and the score has fallen since last time,
            # decrease the interval by the left-over days
            # Otherwise just add 1 as interval delta to increase interval due to unscheduled revision
            if revision_timing == "EARLY_REVISION":
                if line_mistakes > 1 and 60 - score < 60 - last_score:
                    current_interval = (
                        scheduled_interval - (scheduled_due_date - revision_date).days
                    )
                else:
                    interval_delta = 1
        max_interval = get_max_interval(score)

        next_interval = get_next_interval(
            current_interval, interval_delta, max_interval, difficulty_level
        )

        # If the interval is negative or zero, we want to revise the next day
        if next_interval <= 0:
            due_date = revision_date + datetime.timedelta(days=1)
        else:
            due_date = revision_date + datetime.timedelta(days=next_interval)

        page_summary = {
            "1.revision_number": index + 1,
            "2.revision date": revision_date,
            "3.score": score,
            "4.current_interval": current_interval,
            "5.interval_delta": interval_delta,
            "6.max_interval": max_interval,
            "7.scheduled_interval": next_interval,
            "8.scheduled_due_date": due_date,
            "page_strength": round(
                next_interval / (index + 1), 1
            ),  # Interval per revision
            "is_due": due_date <= datetime.date.today(),
            "overdue_days": (due_date - datetime.date.today()).days,
            "mistakes": get_mistakes_text(word_mistakes, line_mistakes),
            "score_cumulative": score_cumulative,
            "score_average": round(score_cumulative / (index + 1), 2),
        }

    # Since this dict will be stored in session,
    # we need to convert datetime objects into a string representation
    new_page_summary = {
        key: value.strftime("%Y-%m-%d") if isinstance(value, datetime.date) else value
        for key, value in page_summary.items()
    }

    return new_page_summary


# TODO change score to a negative
def get_page_score(word_mistakes, line_mistakes):
    # each page has 15 lines - each line is worth 4 points. So, max point is 15*4 = 60
    # Each word mistake takes away 1 point, and each line mistake 4 points.
    # If the total page is gone, the score would be zero.
    # return 60 - word_mistakes * 1 - line_mistakes * 4
    return word_mistakes * 1 + line_mistakes * 4


def get_interval_delta(score):
    # Convert score into an interval delta
    if score == 0:  # Perfect page
        return +3
    elif score == 1:  # 1 Word Mistake
        return +2
    elif score <= 3:  # 3 Word Mistakes
        return +1
    elif score == 4:  # 1 Line Mistake
        return 0
    elif score <= 8:  # 2 Line Mistakes
        return -1
    elif score <= 12:  # 3 Line Mistakes
        return -2
    elif score <= 20:  # 5 Line Mistakes
        return -3
    elif score <= 30:  # 7.5 Line Mistakes - Half a page
        return -5
    else:  # More than half a page
        return -7


def get_max_interval(score):

    # If Score is 8 or more (2 line mistakes or more), then we have to restrict the max Interval
    if score < 4:
        return None
    elif score == 4:  # 1 Line Mistake - 40 days max
        return 40
    elif score <= 8:  # 2 Line Mistakes - 30 days/1 month max
        return 30
    elif score <= 12:  # 3 Line Mistakes - 3 weeks max
        return 21
    elif score <= 20:  # 5 Line Mistakes - 2 weeks max
        return 14
    elif score <= 30:  # 7.5 Line Mistakes - Half a page - 1 week max
        return 7
    else:  # More than half a page - 3 days max
        return 3


def get_next_interval(current_interval, interval_delta, max_interval, difficulty_level):
    next_interval = current_interval + interval_delta

    if difficulty_level == "e":
        if next_interval <= 15:
            next_interval += 5
        elif next_interval <= 30:
            next_interval += 3
        else:
            next_interval += 1

    elif difficulty_level == "h":
        if next_interval >= 20:
            next_interval -= 5
        elif next_interval >= 10:
            next_interval -= 3
        elif next_interval >= 3:
            next_interval -= 1

    # Restrict the next interval to max interval if is smaller
    if max_interval is None or max_interval > next_interval:
        return next_interval
    return max_interval


def update_current_interval_hack(current_interval, student_id, score):
    current_interval = int(current_interval or 0)

    # Temp hack to reduce too-many due pages for Safwan and Hanan
    if student_id == 3:
        current_interval = 10 if score == 0 else 5
    elif student_id == 4:
        current_interval = 15 if score == 0 else 7
    return current_interval


def get_revision_timing(scheduled_due_date, revision_date):
    # ideally the page should be revised on the due date, not before or after
    if scheduled_due_date == revision_date:
        return "ON_TIME_REVISION"
    elif scheduled_due_date < revision_date:
        return "LATE_REVISION"
    else:
        return "EARLY_REVISION"


def get_mistakes_text(word_mistakes, line_mistakes):
    # More readable mistakes string
    mistakes_text = "-"
    if line_mistakes != 0:
        mistakes_text = str(line_mistakes) + "L "

    if word_mistakes != 0:
        if line_mistakes != 0:
            mistakes_text += str(word_mistakes) + "W"
        else:
            mistakes_text = str(word_mistakes) + "W"
    return mistakes_text
