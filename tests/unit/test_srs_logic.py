"""Unit tests for SRS algorithm pure functions in app/srs_reps.py."""

import pytest
from app.srs_reps import (
    binary_search_less_than,
    get_interval_triplet,
    apply_rating_penalty,
    get_next_interval_based_on_rating,
    SRS_START_INTERVAL,
    SRS_INTERVALS,
)


class TestBinarySearchLessThan:
    def test_target_exactly_matches_element(self):
        result = binary_search_less_than([2, 5, 10, 20], 10)
        assert result == {"index": 2, "value": 10}

    def test_target_between_elements_returns_smaller(self):
        result = binary_search_less_than([2, 5, 10, 20], 8)
        assert result == {"index": 1, "value": 5}

    def test_target_smaller_than_all_elements(self):
        result = binary_search_less_than([2, 5, 10, 20], 1)
        assert result == {"index": None, "value": None}

    def test_target_larger_than_all_elements(self):
        result = binary_search_less_than([2, 5, 10, 20], 100)
        assert result == {"index": 3, "value": 20}

    def test_first_element_match(self):
        result = binary_search_less_than([2, 5, 10, 20], 2)
        assert result == {"index": 0, "value": 2}

    def test_last_element_match(self):
        result = binary_search_less_than([2, 5, 10, 20], 20)
        assert result == {"index": 3, "value": 20}

    def test_single_element_list_match(self):
        result = binary_search_less_than([5], 5)
        assert result == {"index": 0, "value": 5}

    def test_single_element_list_smaller(self):
        result = binary_search_less_than([5], 3)
        assert result == {"index": None, "value": None}

    def test_single_element_list_larger(self):
        result = binary_search_less_than([5], 10)
        assert result == {"index": 0, "value": 5}

    def test_with_srs_intervals(self):
        result = binary_search_less_than(SRS_INTERVALS, 30)
        assert result == {"index": 9, "value": 29}


class TestGetIntervalTriplet:
    def test_middle_of_list(self):
        triplet = get_interval_triplet(10, [2, 5, 10, 20, 30])
        assert triplet == [5, 10, 20]

    def test_first_element_left_equals_current(self):
        triplet = get_interval_triplet(2, [2, 5, 10, 20])
        assert triplet == [2, 2, 5]

    def test_last_element_right_equals_current(self):
        triplet = get_interval_triplet(20, [2, 5, 10, 20])
        assert triplet == [10, 20, 20]

    def test_target_not_exactly_in_list(self):
        triplet = get_interval_triplet(8, [2, 5, 10, 20])
        assert triplet == [2, 5, 10]

    def test_target_smaller_than_all_starts_at_index_0(self):
        triplet = get_interval_triplet(1, [2, 5, 10, 20])
        assert triplet == [2, 2, 5]

    def test_target_larger_than_all(self):
        triplet = get_interval_triplet(100, [2, 5, 10, 20])
        assert triplet == [10, 20, 20]

    def test_single_element_list(self):
        triplet = get_interval_triplet(5, [5])
        assert triplet == [5, 5, 5]

    def test_two_element_list_first(self):
        triplet = get_interval_triplet(5, [5, 10])
        assert triplet == [5, 5, 10]

    def test_two_element_list_second(self):
        triplet = get_interval_triplet(10, [5, 10])
        assert triplet == [5, 10, 10]

    def test_with_srs_intervals_prime_sequence(self):
        triplet = get_interval_triplet(29, SRS_INTERVALS)
        assert triplet == [23, 29, 31]


class TestApplyRatingPenalty:
    @pytest.mark.parametrize(
        "actual_interval,rating,expected",
        [
            (100, 1, 100),
            (10, 1, 10),
            (1, 1, 1),
        ],
    )
    def test_good_rating_100_percent(self, actual_interval, rating, expected):
        assert apply_rating_penalty(actual_interval, rating) == expected

    @pytest.mark.parametrize(
        "actual_interval,rating,expected",
        [
            (100, 0, 50),
            (10, 0, 5),
            (1, 0, 0),
        ],
    )
    def test_ok_rating_50_percent(self, actual_interval, rating, expected):
        assert apply_rating_penalty(actual_interval, rating) == expected

    @pytest.mark.parametrize(
        "actual_interval,rating,expected",
        [
            (100, -1, 35),
            (10, -1, 4),
            (1, -1, 0),
        ],
    )
    def test_bad_rating_35_percent(self, actual_interval, rating, expected):
        assert apply_rating_penalty(actual_interval, rating) == expected

    def test_rounding_behavior_rounds_half_up(self):
        assert apply_rating_penalty(3, 0) == 2
        assert apply_rating_penalty(5, 0) == 2
        assert apply_rating_penalty(7, 0) == 4

    def test_rounding_for_bad_rating(self):
        assert apply_rating_penalty(20, -1) == 7
        assert apply_rating_penalty(30, -1) == 10


class TestGetNextIntervalBasedOnRating:
    def test_bad_rating_moves_left(self):
        result = get_next_interval_based_on_rating(29, -1)
        assert result == 23

    def test_ok_rating_stays_at_current(self):
        result = get_next_interval_based_on_rating(29, 0)
        assert result == 29

    def test_good_rating_moves_right(self):
        result = get_next_interval_based_on_rating(29, 1)
        assert result == 31

    def test_at_first_element_bad_rating_stays(self):
        result = get_next_interval_based_on_rating(2, -1)
        assert result == 2

    def test_at_last_element_good_rating_stays(self):
        result = get_next_interval_based_on_rating(101, 1)
        assert result == 101

    def test_target_not_in_list_uses_closest_lower(self):
        result = get_next_interval_based_on_rating(30, 1)
        assert result == 31


class TestSrsStartInterval:
    def test_bad_rating_starts_at_3_days(self):
        assert SRS_START_INTERVAL[-1] == 3

    def test_ok_rating_starts_at_10_days(self):
        assert SRS_START_INTERVAL[0] == 10
