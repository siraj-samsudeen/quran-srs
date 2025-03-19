from datetime import datetime
import re
import humanize


# Util function
def standardize_column(column_name):
    cleaned_column = column_name.strip().lower()
    # Replace consecutive spaces with a single underscore
    return re.sub(r"\s+", "_", cleaned_column)


def current_time(f="%Y-%m-%d %I:%M %p"):
    return datetime.now().strftime(f)


def compact_format(numbers):
    if not numbers:
        return ""

    # Remove duplicates while maintaining ascending order
    unique_numbers = sorted(set(numbers))

    result = []
    start = unique_numbers[0]
    end = unique_numbers[0]

    for num in unique_numbers[1:] + [None]:  # Add sentinel value
        if num is not None and num == end + 1:
            # Continue the current range
            end = num
        else:
            # Add the completed range to the result
            if start == end:
                result.append(str(start))
            else:
                result.append(f"{start}-{end}")

            # Start a new range (if not at the end)
            if num is not None:
                start = end = num

    return ", ".join(result)


def date_to_human_readable(date_string):

    try:
        # Parse the input date string
        input_date = datetime.strptime(date_string, "%Y-%m-%d")
    except ValueError:
        # Return the original string if it can't be parsed
        return date_string

    # Convert the date to a human-readable format
    return humanize.naturaldate(input_date).capitalize()
