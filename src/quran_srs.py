import datetime
import os
import pprint
import sys
from collections import defaultdict
from contextlib import contextmanager
from pathlib import Path
from collections import namedtuple

import dateparser

# ezsheets is the easy way to connect to Google sheets written by Al Sweigart
import ezsheets


class PAGE_REVISION:
    revision_date = "revision_date"
    word_mistakes = "word_mistakes"
    line_mistakes = "line_mistakes"
    current_interval = "current_interval"


@contextmanager
def using_revision_data(directory):
    current_dir = os.getcwd()
    os.chdir(directory)
    yield download_revision_data()
    os.chdir(current_dir)


def download_revision_data():
    GOOGLE_SHEET_ID = "114LWy42iuyzIfKFrg-egp2o6jT-2XrnkzrYFSqmweOE"
    google_sheet = ezsheets.Spreadsheet(GOOGLE_SHEET_ID)

    # Get the first sheet that contains the form responses for Quran Review data
    input_sheet = google_sheet[0]
    return input_sheet.getRows(2, input_sheet.rowCount - +1)


def expand_revision_data(revision_data):
    # This dictionary is going to hold a list of revisions for each page
    revision_list_by_page = defaultdict(list)

    for (
        revision_date,
        page,
        word_mistakes,
        line_mistakes,
        current_interval,
    ) in revision_data:
        # exit when an empty row is encountered
        if revision_date == "":
            break

        # Assign the columns to proper variable names
        revision_date = dateparser.parse(revision_date)

        # since each of these column can have an empty string,
        # we can ask int function to return 0 if it finds an empty string
        word_mistakes = int(word_mistakes or 0)
        line_mistakes = int(line_mistakes or 0)
        current_interval = int(current_interval or 0)

        # A single page number is entered directly
        if page.isdecimal():
            revision_list_by_page[page].append(
                {
                    PAGE_REVISION.revision_date: revision_date,
                    PAGE_REVISION.word_mistakes: word_mistakes,
                    PAGE_REVISION.line_mistakes: line_mistakes,
                    PAGE_REVISION.current_interval: current_interval,
                }
            )

        # More than one page is entered using this format p1-p2
        # (p1 is the starting page, p2 is ending page) e.g."420-425"
        else:
            if "-" in page:
                # Get the start and end page number from the combined string and
                # convert them into a number
                start_page, end_page = page.split("-")
                start_page = int(start_page or 0)
                end_page = int(end_page or 0)
                # Convert the page to a string for consistency
                page_list = [str(i) for i in range(start_page, end_page + 1)]
            else:  # the list is comma-separated p1,p2,p3, etc.
                page_list = page.split(",")

            for page in page_list:
                revision_list_by_page[page].append(
                    {
                        PAGE_REVISION.revision_date: revision_date,
                        PAGE_REVISION.word_mistakes: word_mistakes,
                        PAGE_REVISION.line_mistakes: line_mistakes,
                        PAGE_REVISION.current_interval: current_interval,
                    }
                )
    return revision_list_by_page


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


def get_next_interval(current_interval, interval_delta, max_interval):
    next_interval = current_interval + interval_delta

    # Restrict the next interval to max interval if is smaller
    if max_interval is None or max_interval > next_interval:
        return next_interval
    return max_interval


def extract_record(revision):
    return (
        revision[PAGE_REVISION.revision_date],
        revision[PAGE_REVISION.word_mistakes],
        revision[PAGE_REVISION.line_mistakes],
        revision[PAGE_REVISION.current_interval],
    )


def process_page(page, revision_list, extract_record):
    page_summary = {}
    for index, revision in enumerate(revision_list):
        (
            revision_date,
            word_mistakes,
            line_mistakes,
            current_interval,
        ) = extract_record(revision)
        score = get_page_score(word_mistakes, line_mistakes)

        # Since revision_date was a datetime object, it was causing a subtle bug
        # in determining revision timings. Even on the due date,
        # it is flagging some revisions as EARLY based on the timestamp
        revision_date = revision_date.date()
        interval_delta = INTERVAL_DELTAS[score]

        # This is first revision - Hence, the page can be new or can have a current interval
        # Take the current interval in the input data or make it zero
        if index == 0:
            current_interval = int(current_interval or 0)
        else:
            # We have the summary data from earlier revisions, hence we have to take use them
            page_summary_dict = page_summary
            scheduled_interval = page_summary_dict.get("7.scheduled_interval")
            scheduled_due_date = page_summary_dict.get("8.scheduled_due_date")
            last_score = page_summary_dict.get("3.score")

            # class REVESION_TIMING(Enum):
            #     ON_TIME_REVISION =0
            #     LATE_REVISION =1
            #     EARLY_REVISION=-1
            # ideally the page should be revised on the due date, not before or after
            if scheduled_due_date == revision_date:
                revision_timing = "ON_TIME_REVISION"
            elif scheduled_due_date < revision_date:
                revision_timing = "LATE_REVISION"
            else:
                revision_timing = "EARLY_REVISION"

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
                # print("page ", page, revision_timing, 'IMPROVED','score =', score, "last_score", last_score)

            # For Early Revisions
            # If the score has fallen since last time, decrease the interval by the left-over days
            # Otherwise don't change the interval, just postpone the due date
            if revision_timing == "EARLY_REVISION":
                if 60 - score < 60 - last_score:
                    current_interval = (
                        scheduled_interval - (scheduled_due_date - revision_date).days
                    )
                    # print("page ", page, revision_timing, 'DECLINE','score =', score, "last_score", last_score)
                else:
                    interval_delta = 0
        max_interval = MAX_INTERVALS[score]
        next_interval = get_next_interval(
            current_interval, interval_delta, max_interval
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
            "days_due": (due_date - datetime.date.today()).days,
            "mistakes": mistakes_text,
        }

    # Since this dict will be stored in session,
    # we need to convert datetime objects into a string representation
    new_page_summary = {
        key: value.strftime("%Y-%m-%d %H:%M") if type(value) == datetime.date else value
        for key, value in page_summary.items()
    }

    return new_page_summary


def process_revision_data(revision_list_by_page, extract_record):
    # we want to store the summary information about each page as we process revision data in a dict
    summary_by_page = defaultdict(dict)

    if hasattr(revision_list_by_page, "items"):
        revision_list_by_page = revision_list_by_page.items()
    for page, revision_list in revision_list_by_page:
        page_summary = process_page(page, revision_list, extract_record)
        summary_by_page[page] = page_summary
    return summary_by_page


def calculate_due_pages(summary_by_page):
    page_by_due_date = defaultdict(list)
    due_pages_list = []
    for page, page_summary_dict in summary_by_page.items():
        scheduled_due_date = page_summary_dict.get("8.scheduled_due_date")
        page_by_due_date[str(scheduled_due_date)].append(page)
        if scheduled_due_date.date() <= datetime.date.today():
            # + datetime.timedelta(    days=1       ):
            due_pages_list.append(page)

    return page_by_due_date, due_pages_list


def write_output_due(due_pages_list, summary_by_page):
    output_spreadsheet = ezsheets.Spreadsheet(
        "1rHQ5WmyFz79sG8W2pNZmr6AJDuLuQEeOjSahPyPcb5o"
    )

    # First write the due pages sheet
    output_sheet = output_spreadsheet["Due"]

    print("Writing sheet - Due")

    # empty the sheet
    for i in range(7):
        output_sheet.updateColumn(i + 1, [])
    row = 1

    column_names = ["page", "due", "interval", "revision#", "score", "rating"]
    output_sheet.updateRow(row, column_names)

    for due_page in sorted(
        due_pages_list,
        key=lambda page: int(page)
        # (
        #     round(
        #         summary_by_page[page]["7.scheduled_interval"]
        #         / summary_by_page[page]["1.revision_number"],
        #         0,
        #     ),
        #     int(page),
        # ),
    ):
        summary = summary_by_page[due_page]
        columns = [
            due_page,
            (summary["8.scheduled_due_date"].date() - datetime.date.today()).days,
            summary["7.scheduled_interval"],
            summary["1.revision_number"],
            summary["3.score"],
            summary["7.scheduled_interval"] / summary["1.revision_number"],
        ]
        print(row, columns)
        row += 1
        output_sheet.updateRow(row, columns)

    output_sheet.updateRow(
        row + 1,
        ["Done", "", "", "", "", "", datetime.datetime.now().strftime("%d-%m %H:%M")],
    )


if __name__ == "__main__":
    # Google sheets needs the credentials files to be in the same folder as the program
    # If the python file is in a different location than credentials, then the path of the credentials file should be passed
    # as an argument. If nothing is passed, we assume that the credentials is in the same folder as the python program
    try:
        directory = sys.argv[1]
    except IndexError:
        directory = Path(__file__).absolute().parent

    with using_revision_data(directory) as data:
        rev_data = expand_revision_data(data)
        summary_by_page = process_revision_data(rev_data, extract_record)
        _, due_pages_list = calculate_due_pages(summary_by_page)
        write_output_due(due_pages_list, summary_by_page)

    print("SRS Done")
