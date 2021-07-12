import datetime
from collections import defaultdict


def get_page_score(word_mistakes, line_mistakes):
    # each page has 15 lines - each line is worth 4 points. So, max point is 15*4 = 60
    # Each word mistake takes away 1 point, and each line mistake 4 points.
    # If the total page is gone, the score would be zero.
    # return 60 - word_mistakes * 1 - line_mistakes * 4
    return word_mistakes * 1 + line_mistakes * 4


INTERVAL_DELTAS = defaultdict(
    lambda: -7,
    {
        0: 3,
        1: 2,
        **{x: 1 for x in (2, 3)},
        4: 0,
        **{x: -1 for x in (5, 6, 7, 8)},
        # Just a different way of doing to learn
        **dict.fromkeys((9, 10, 11, 12), -2),
        **{x: -3 for x in range(13, 21)},
        **{x: -5 for x in range(21, 31)},
    },
)

MAX_INTERVALS = defaultdict(
    lambda: 3,  # More than half a page - 3 days max
    {
        **{x: None for x in range(0, 4)},
        # 1 Line Mistake - 40 days max
        4: 40,
        # 2 Line Mistakes - 30 days/1 month max
        **{x: 30 for x in range(5, 9)},
        # 3 Line Mistakes - 3 weeks max
        **{x: 21 for x in range(9, 13)},
        # 5 Line Mistakes - 2 weeks ma
        **{x: 14 for x in range(13, 21)},
        # 7.5 Line Mistakes - Half a page - 1 week max
        **{x: 7 for x in range(21, 31)},
    },
)


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


def update_current_interval(current_interval, student_id, score):
    current_interval = int(current_interval or 0)

    # Temp hack to reduce too-many due pages for Safwan and Hanan
    if student_id == 4:
        if score == 0:
            current_interval = 15
        else:
            current_interval = 7
    if student_id == 3:
        if score == 0:
            current_interval = 10
        else:
            current_interval = 5

    return current_interval


def get_revision_timing(scheduled_due_date, revision_date):
    # ideally the page should be revised on the due date, not before or after
    if scheduled_due_date == revision_date:
        revision_timing = "ON_TIME_REVISION"
    elif scheduled_due_date < revision_date:
        revision_timing = "LATE_REVISION"
    else:
        revision_timing = "EARLY_REVISION"
    return revision_timing


def process_page(revision_list, student_id):
    page_summary = {}
    for index, revision in enumerate(revision_list):
        # Since revision_date was a datetime object, it was causing a subtle bug
        # in determining revision timings. Even on the due date,
        # it is flagging some revisions as EARLY based on the timestamp
        revision_date = revision["date"].date()
        word_mistakes = revision["word_mistakes"]
        line_mistakes = revision["line_mistakes"]
        current_interval = revision["current_interval"]
        difficulty_level = revision["difficulty_level"]

        score = get_page_score(word_mistakes, line_mistakes)

        interval_delta = INTERVAL_DELTAS[score]

        # This is first revision - Hence, the page can be new or can have a current interval
        # Take the current interval in the input data or make it zero
        if index == 0:
            current_interval = update_current_interval(
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
        max_interval = MAX_INTERVALS[score]

        next_interval = get_next_interval(
            current_interval, interval_delta, max_interval, difficulty_level
        )

        # If the interval is negative or zero, we want to revise the next day
        if next_interval <= 0:
            due_date = revision_date + datetime.timedelta(days=1)
        else:
            due_date = revision_date + datetime.timedelta(days=next_interval)

        # More readable mistakes string
        mistakes_text = "-"
        if line_mistakes != 0:
            mistakes_text = str(line_mistakes) + "L "

        if word_mistakes != 0:
            if line_mistakes != 0:
                mistakes_text += str(word_mistakes) + "W"
            else:
                mistakes_text = str(word_mistakes) + "W"

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
            "mistakes": mistakes_text,
            "score_cumulative": score_cumulative,
            "score_average": round(score_cumulative / (index + 1), 2),
        }

    # Issue #13 - Stop pages from coming for revision on 2 consecutive days
    if (due_date - revision_date).days == 1:
        due_date = due_date + datetime.timedelta(days=1)
        page_summary["8.scheduled_due_date"] = due_date

    # Since this dict will be stored in session,
    # we need to convert datetime objects into a string representation
    new_page_summary = {
        key: value.strftime("%Y-%m-%d") if isinstance(value, datetime.date) else value
        for key, value in page_summary.items()
    }

    return new_page_summary


def process_revision_data(revision_list_by_page, student_id):
    # we want to store the summary information about each page as we process revision data in a dict
    summary_by_page = defaultdict(dict)

    if hasattr(revision_list_by_page, "items"):
        revision_list_by_page = revision_list_by_page.items()
    for page, revision_list in revision_list_by_page:
        page_summary = process_page(revision_list, student_id)
        summary_by_page[page] = page_summary
    return summary_by_page
