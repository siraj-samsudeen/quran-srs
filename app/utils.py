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


def add_days_to_date(date_str, days):
    date_obj = datetime.strptime(date_str, "%Y-%m-%d")
    new_date = date_obj + timedelta(days=days)
    return new_date.strftime("%Y-%m-%d")


def sub_days_to_date(date_str, days):
    date_obj = datetime.strptime(date_str, "%Y-%m-%d")
    new_date = date_obj - timedelta(days=days)
    return new_date.strftime("%Y-%m-%d")


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


def set_zero_to_none(data):
    if data == 0:
        return None
    return data


def format_number(num):
    num = float(num)
    rounded = round(num, 1)
    return int(rounded) if rounded.is_integer() else rounded


def find_gaps(input_list, master_list):
    """Find gaps in input_list relative to master_list. Returns list of (before_gap, after_gap) tuples."""
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
    """Return days between two dates (positive if date2 > date1)."""
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


def render_date(date: str):
    if date:
        date = date_to_human_readable(date)
    return date


def get_day_from_date(date: str):
    if date:
        return datetime.strptime(date, "%Y-%m-%d").day
