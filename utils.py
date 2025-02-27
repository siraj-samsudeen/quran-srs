from datetime import datetime
import re


# Util function
def standardize_column(column_name):
    cleaned_column = column_name.strip().lower()
    # Replace consecutive spaces with a single underscore
    return re.sub(r"\s+", "_", cleaned_column)


def current_time(f="%Y-%m-%d %I:%M %p"):
    return datetime.now().strftime(f)


def convert_time(t, reverse=False):
    initial = "%Y-%m-%d"
    end = "%d %b %Y"
    if reverse:
        initial, end = end, initial
    try:
        return datetime.strptime(t, initial).strftime(end)
    except ValueError:
        return None
