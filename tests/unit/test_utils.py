"""Unit tests for utils.py pure functions."""

import pytest
from utils import (
    flatten_list,
    find_next_greater,
    compact_format,
    day_diff,
    calculate_days_difference,
    find_gaps,
    format_number,
    date_to_human_readable,
    table_to_dataclass_name,
)


class TestFlattenList:
    def test_flattens_nested_lists(self):
        assert flatten_list([[1, 2], [3, 4]]) == [1, 2, 3, 4]


class TestFindNextGreater:
    def test_finds_next_greater(self):
        assert find_next_greater([1, 3, 5, 7], 3) == 5

    def test_returns_none_when_no_greater(self):
        assert find_next_greater([1, 3, 5], 5) is None

    def test_target_not_in_list(self):
        assert find_next_greater([1, 3, 5, 7], 4) == 5

    def test_empty_list(self):
        assert find_next_greater([], 5) is None

    def test_first_element(self):
        assert find_next_greater([1, 3, 5], 0) == 1


class TestCompactFormat:
    def test_consecutive_numbers(self):
        assert compact_format([1, 2, 3, 4, 5]) == "1-5"

    def test_single_number(self):
        assert compact_format([5]) == "5"

    def test_non_consecutive(self):
        assert compact_format([1, 3, 5]) == "1, 3, 5"

    def test_mixed(self):
        assert compact_format([1, 2, 3, 7, 8, 9, 15]) == "1-3, 7-9, 15"

    def test_empty_list(self):
        assert compact_format([]) == ""

    def test_duplicates_removed(self):
        assert compact_format([1, 1, 2, 2, 3]) == "1-3"


class TestDayDiff:
    def test_empty_date1(self):
        assert day_diff("", "2024-01-15") == 0

    def test_empty_date2(self):
        assert day_diff("2024-01-15", "") == 0

    def test_none_date1(self):
        assert day_diff(None, "2024-01-15") == 0

    def test_none_date2(self):
        assert day_diff("2024-01-15", None) == 0


class TestCalculateDaysDifference:
    def test_invalid_format_raises(self):
        with pytest.raises(ValueError):
            calculate_days_difference("invalid", "2024-01-01")

    def test_empty_date_raises(self):
        with pytest.raises(ValueError):
            calculate_days_difference("", "2024-01-01")

    def test_none_date_raises(self):
        with pytest.raises(TypeError):
            calculate_days_difference(None, "2024-01-01")


class TestFindGaps:
    def test_no_gaps(self):
        assert find_gaps([1, 2, 3], [1, 2, 3]) == []

    def test_gap_in_middle(self):
        result = find_gaps([1, 3], [1, 2, 3])
        assert (1, 3) in result

    def test_continuation_at_end(self):
        result = find_gaps([1, 2], [1, 2, 3, 4])
        assert (2, None) in result

    def test_empty_input(self):
        assert find_gaps([], [1, 2, 3]) == []


class TestFormatNumber:
    def test_integer_result(self):
        assert format_number(5.0) == 5

    def test_rounds_to_one_decimal(self):
        assert format_number(5.67) == 5.7


class TestDateToHumanReadable:
    def test_valid_date(self):
        result = date_to_human_readable("2024-01-15")
        assert "Jan" in result
        assert "15" in result

    def test_invalid_date_returns_original(self):
        assert date_to_human_readable("invalid") == "invalid"


class TestTableToDataclassName:
    def test_simple_plural(self):
        assert table_to_dataclass_name("hafizs") == "Hafiz"
        assert table_to_dataclass_name("items") == "Item"
        assert table_to_dataclass_name("modes") == "Mode"

    def test_compound_name(self):
        assert table_to_dataclass_name("hafizs_items") == "Hafiz_Items"
