from app.common_function import get_interval_triplet

srs_intervals = [
    2,
    3,
    5,
    7,
    11,
    13,
    17,
    19,
    23,
    29,
    31,
    37,
    41,
    43,
    47,
    53,
    59,
    61,
    67,
    71,
    73,
    79,
    83,
    89,
    97,
    101,
]


def test_srs_intervals_exact_match():
    """Test when current_interval exactly matches a prime"""

    # Test exact match - should trigger edge case
    result = get_interval_triplet(7, srs_intervals)
    expected = [5, 7, 11]  # Based on your edge case rule
    assert result == expected


def test_srs_intervals_between_values():
    """Test when current_interval falls between primes"""

    # Test between values
    result = get_interval_triplet(12, srs_intervals)
    expected = [7, 11, 13]
    assert result == expected


def test_edge_case_first_element():
    """Test edge case at beginning of list"""

    # Test first element
    result = get_interval_triplet(2, srs_intervals)
    expected = [2, 2, 3]  # Edge case behavior
    assert result == expected


def test_exact_match_last_element():
    """Test when current_interval exactly matches the last element"""

    # Test exact match with last element
    result = get_interval_triplet(101, srs_intervals)
    expected = [
        97,
        101,
        101,
    ]  # Right value repeats last element when no next element exists
    assert result == expected


def test_value_beyond_last_element():
    """Test when current_interval exceeds all elements in the list"""

    # Test value higher than last element
    result = get_interval_triplet(105, srs_intervals)
    expected = [97, 101, 101]  # Uses last element when target > all elements
    assert result == expected


def test_simple_list_cases():
    """Test with simpler lists for clearer logic verification"""
    simple_list = [1, 3, 5, 7, 9]

    # Normal case
    result1 = get_interval_triplet(4, simple_list)
    expected1 = [1, 3, 5]
    assert result1 == expected1

    # Edge case - exact match
    result2 = get_interval_triplet(5, simple_list)
    expected2 = [3, 5, 7]
    assert result2 == expected2
