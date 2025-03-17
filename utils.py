from datetime import datetime
import re


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

        # Get today's date without time information
        today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)

        # Strip time information from input date
        input_date = input_date.replace(hour=0, minute=0, second=0, microsecond=0)

        # Calculate difference in days
        day_diff = (today - input_date).days

        # Return appropriate string based on day difference
        if day_diff == 0:
            return "Today"
        elif day_diff == 1:
            return "Yesterday"
        else:
            # Return the original date string for dates beyond 2 days ago
            return date_string
