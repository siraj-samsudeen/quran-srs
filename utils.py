from datetime import datetime, timedelta
import bisect
import re
import sqlite3
import os
import itertools

def flatten_list(list_of_lists):
    return list(itertools.chain(*list_of_lists))


def find_next_greater(arr, target):
    # Find insertion point for target
    pos = bisect.bisect_right(arr, target)
    if pos < len(arr):
        return arr[pos]
    return None


def select_all_with_shift_click_for_summary_table(class_name):
    template = """
        {
        selectAll: false,
        updateSelectAll() {
            const checkboxes = [...$el.querySelectorAll('.CLASS_NAME_PLACEHOLDER')];
          this.selectAll = checkboxes.length > 0 && checkboxes.every(cb => cb.checked);
        },
        toggleAll() {
          $el.querySelectorAll('.CLASS_NAME_PLACEHOLDER').forEach(cb =>  {
            cb.checked = this.selectAll;
        });
        },
        handleCheckboxClick(e) {
            // Handle shift+click selection
            if (e.shiftKey) {
                const checkboxes = [...$el.querySelectorAll('.CLASS_NAME_PLACEHOLDER')];
                const currentCheckboxIndex = checkboxes.indexOf(e.target);
                
                // loop through the checkboxes backwards untll we find one that is checked
                for (let i = currentCheckboxIndex; i >= 0; i--) {
                    if (i != currentCheckboxIndex && checkboxes[i].checked) {break;}
                    checkboxes[i].checked = true;
                     // Trigger change event for each modified checkbox
                    const event = new Event('change', {
                        bubbles: true, 
                        cancelable: true
                    });
                    checkboxes[i].dispatchEvent(event);
                }
            }
            this.updateSelectAll();
        },
        }
    """
    return template.replace("CLASS_NAME_PLACEHOLDER", class_name)


def select_all_checkbox_x_data(class_name, is_select_all="true"):
    template = """
        { 
        selectAll: SELECT_ALL_PLACEHOLDER,
        globalDropdownValue: '', // Store the global dropdown selection
        updateSelectAll() {
            const checkboxes = [...$el.querySelectorAll('.CLASS_NAME_PLACEHOLDER')];
          this.selectAll = checkboxes.length > 0 && checkboxes.every(cb => cb.checked);
        },
        toggleAll() {
          $el.querySelectorAll('.CLASS_NAME_PLACEHOLDER').forEach(cb => {
            cb.checked = this.selectAll;
          });
        },
        handleCheckboxClick(e) {
            // Handle shift+click selection
            if (e.shiftKey) {
                const checkboxes = [...$el.querySelectorAll('.CLASS_NAME_PLACEHOLDER')];
                const currentCheckboxIndex = checkboxes.indexOf(e.target);
                
                // loop through the checkboxes backwards untll we find one that is checked
                for (let i = currentCheckboxIndex; i >= 0; i--) {
                    if (i != currentCheckboxIndex && checkboxes[i].checked) {break;}
                    checkboxes[i].checked = true;
                }
            }
            this.updateSelectAll();
        },
        // this function will update the selected checkbox row with the global dropdown value
       applyGlobalValue() {
        if (!this.globalDropdownValue) {
            alert('Please select a value from the global dropdown first.');
            return;
        }
        
        // Get all checked checkboxes
        const checkedCheckboxes = [...$el.querySelectorAll('.CLASS_NAME_PLACEHOLDER:checked')];
        
        if (checkedCheckboxes.length === 0) {
            alert('Please select at least one row to apply the global value.');
            return;
        }
        
        checkedCheckboxes.forEach(checkbox => {
            const row = checkbox.closest('tr');
            const rowDropdown = row.querySelector('select'); // Adjust selector as needed    
            if (rowDropdown) {
                rowDropdown.value = this.globalDropdownValue;
            }
        });
        
    },
    // This function will update the globalDropdownValue
    updateGlobalDropdownValue(e) {
          this.globalDropdownValue = e.target.value;
    }
    }
    """

    return template.replace("CLASS_NAME_PLACEHOLDER", class_name).replace(
        "SELECT_ALL_PLACEHOLDER", is_select_all
    )


# Util function
def standardize_column(column_name):
    cleaned_column = column_name.strip().lower()
    # Replace consecutive spaces with a single underscore
    return re.sub(r"\s+", "_", cleaned_column)


def destandardize_text(text):
    # Replace underscores with spaces
    text = text.replace("_", " ")
    # Capitalize the first letter of each word
    return text.title()


def current_time(f="%Y-%m-%d"):
    return datetime.now().strftime(f)


def calculate_date_difference(days=0, date_format="%Y-%m-%d"):
    current_date = datetime.now()
    target_date = current_date - timedelta(days=days)
    return target_date.strftime(date_format)


def add_days_to_date(date_str, days):
    date_obj = datetime.strptime(date_str, "%Y-%m-%d")
    new_date = date_obj + timedelta(days=days)
    return new_date.strftime("%Y-%m-%d")


def sub_days_to_date(date_str, days):
    date_obj = datetime.strptime(date_str, "%Y-%m-%d")
    new_date = date_obj - timedelta(days=days)
    return new_date.strftime("%Y-%m-%d")


def is_first_date_greater(
    date1: str, date2: str, date_format: str = "%Y-%m-%d"
) -> bool:
    try:
        d1 = datetime.strptime(date1, date_format)
        d2 = datetime.strptime(date2, date_format)
        return d1 >= d2
    except ValueError as e:
        raise ValueError(f"Invalid date format. Error: {str(e)}")


# TODO: this function is duplixcation of the `calculate_days_difference``
def day_diff(date1, date2):
    """
    Returns the difference in days between two dates (YYYY-MM-DD).
    The result is always non-negative (absolute value).
    """
    if date1 in ["", None] or date2 in ["", None]:
        return 0

    date1 = datetime.strptime(date1, "%Y-%m-%d")
    date2 = datetime.strptime(date2, "%Y-%m-%d")
    return (date2 - date1).days


def calculate_week_number(initial_date, input_date):
    """
    Calculate which week the input_date belongs to based on the initial_date.
    The initial_date is excluded - counting starts from the next day.

    Args:
        initial_date (str): Starting date in DD-MM-YYYY format (excluded from counting)
        input_date (str): Date to check in DD-MM-YYYY format

    Returns:
        int: Week number (1-based)

    Logic:
        - initial_date is excluded from counting
        - Days 1-7 after initial_date = Week 1
        - Days 8-14 after initial_date = Week 2
        - And so on...
    """

    # Parse the date strings
    initial = datetime.strptime(initial_date, "%Y-%m-%d")
    input_dt = datetime.strptime(input_date, "%Y-%m-%d")

    # Calculate the difference in days
    days_diff = (input_dt - initial).days

    # If input_date is same as or before initial_date, return 0
    if days_diff <= 0:
        return 0  # initial_date and earlier dates are not part of any week

    # Calculate week number (1-based)
    # Since we exclude initial_date, day 1 after initial_date starts week 1
    week_number = ((days_diff - 1) // 7) + 1

    return week_number


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
    return input_date.strftime("%b %d %a")


def backup_sqlite_db(source_db_path, backup_dir):
    # Create backup directory if it doesn't exist
    os.makedirs(backup_dir, exist_ok=True)

    # Generate backup filename with timestamp
    timestamp = current_time("%Y%m%d_%H%M%S")
    db_name = os.path.basename(source_db_path)
    backup_name = f"{os.path.splitext(db_name)[0]}_{timestamp}.db"
    backup_path = os.path.join(backup_dir, backup_name)

    # Connect to source database
    source = sqlite3.connect(source_db_path)

    # Connect to destination database (will create it if it doesn't exist)
    destination = sqlite3.connect(backup_path)

    # Use SQLite's backup API to create the backup
    source.backup(destination)

    # Close connections
    source.close()
    destination.close()

    return backup_path


def insert_between(lst, element):
    """
    Insert an element between every pair of elements in a list.

    Args:
        lst: The original list
        element: The element to insert between each pair

    Returns:
        A new list with the element inserted between each pair
    """
    if len(lst) <= 1:
        return lst.copy()

    result = []
    for i in range(len(lst)):
        result.append(lst[i])
        if i < len(lst) - 1:  # Don't add separator after last element
            result.append(element)

    return result


def set_zero_to_none(data):
    if data == 0:
        return None
    return data


def format_number(num):
    num = float(num)
    rounded = round(num, 1)
    return int(rounded) if rounded.is_integer() else rounded


# This function is used to get the gaps in a list of numbers.
# This is mainly used for continuation logic
def find_gaps(input_list, master_list):
    """
    Find gaps by identifying the last number before each gap in the sequence.

    Args:
        input_list: List of numbers to check for gaps
        master_list: Master list containing all possible valid numbers

    Returns:
        List of tuples representing gaps, where:
        - First element is the last number before the gap
        - Second element is the next number in input_list after the gap (or None if at the end)
    """
    result = []

    if not input_list:
        return result

    # Sort lists and convert master to set for efficient lookup
    input_sorted = sorted(input_list)
    master_set = set(master_list)

    # Check for gaps between consecutive numbers in input_list
    for i in range(len(input_sorted) - 1):
        current = input_sorted[i]
        next_num = input_sorted[i + 1]

        # Check if there's a gap between current and next_num
        # A gap exists if there are master numbers between them
        gap_exists = False
        for check_num in range(current + 1, next_num):
            if check_num in master_set:
                gap_exists = True
                break

        if gap_exists:
            result.append((current, next_num))

    # Check if there's a potential continuation after the last number
    # This handles the business case where None indicates "use default upper limit"
    last_num = input_sorted[-1]

    # Check if there are numbers in master_list that come after last_num
    # This suggests the sequence could continue
    has_continuation = any(num > last_num for num in master_set)

    if has_continuation:
        result.append((last_num, None))

    return result


def calculate_days_difference(date1_str, date2_str, date_format="%Y-%m-%d"):
    """
    Calculate the difference in days between two dates.

    Args:
        date1_str (str): First date as string
        date2_str (str): Second date as string
        date_format (str): Format of the date strings (default: '%Y-%m-%d')

    Returns:
        int: Number of days between the dates (positive if date2 > date1, negative if date2 < date1)

    Example:
        >>> calculate_days_difference('2024-01-01', '2024-01-10')
        9
        >>> calculate_days_difference('2024-01-10', '2024-01-01')
        -9
    """
    try:
        # Parse the date strings into datetime objects
        date1 = datetime.strptime(date1_str, date_format)
        date2 = datetime.strptime(date2_str, date_format)

        # Calculate the difference
        difference = date2 - date1

        # Return the difference in days
        return difference.days

    except ValueError as e:
        raise ValueError(
            f"Invalid date format. Expected format: {date_format}. Error: {e}"
        )


# This function is only used for getting the intervals for the rating in srs mode
def get_interval_triplet(current_interval, interval_list):
    """
    Returns a triplet [left_sibling, lookup_value, right_sibling] based on the current_interval
    and interval_list.

    Args:
        current_interval: The lookup value (either < min value or present in the list)
        interval_list: List of intervals (assumed to be sorted)

    Returns:
        List of three elements: [left_sibling, lookup_value, right_sibling]
    """
    if not interval_list:
        return [current_interval, current_interval, current_interval]

    # Case 1: current_interval < min value of the list
    if current_interval < interval_list[0]:
        return [current_interval, current_interval, interval_list[0]]

    # Case 2: current_interval is present in the list
    for i in range(len(interval_list)):
        if current_interval == interval_list[i]:
            left = interval_list[i - 1] if i > 0 else interval_list[i]
            right = interval_list[i + 1] if i < len(interval_list) - 1 else "Finished"
            return [left, interval_list[i], right]

    # This shouldn't happen based on the given constraints
    return [current_interval, current_interval, current_interval]


def render_date(date: str):
    if date:
        date = date_to_human_readable(date)
    return date
