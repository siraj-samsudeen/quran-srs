def group_consecutive_pages(pages):
    """
    Algorithm:
    Part 1 - Break the list into a number of nested list with each one containing consecutive pages
    e.g. [112, 113, 115] becomes [ [112, 113], [115] ]
    1. sort the list
    2. for each item in the list
        - check whether the previous item is a consecutive page
        - if no, then add a new nested list with this page.
        - Later, if consecutive pages come, this nested list would be expanded.
        - if it is a consecutive page, then add that page to the last nested list
        - this works since the list is sorted

    Part 2 - Convert this list into a dict
    e.g. [ [112, 113], [115] ] becomes {
        112: [112, 113],
        113: [112, 113],
        115: [115]
    }

    for each nested list
        - create a dict from keys
        - then for each key, populate the nested list as the value
    >>> group_consecutive_pages([112, 113, 115])
    {112: [112, 113], 113: [112, 113], 115: [115]}
    """
    pages = list(pages)

    # PART 1
    groups = bucket_consecutive_pages(pages)

    # PART 2
    result = {}
    for group in groups:
        result.update(dict.fromkeys(group, group))
    return result


def bucket_consecutive_pages(pages):
    groups = []
    pages = sorted(pages)
    for i, page in enumerate(pages):
        if pages[i - 1] == page - 1:
            groups[-1].append(page)
        else:
            groups.append([page])
    return groups


def format_consecutive_pages(consecutive_pages):
    if not consecutive_pages:
        return {}
    max_size = max(len(value) for value in consecutive_pages.values())
    number_of_digits = len(str(max_size))
    return {
        key: (value[0], value[-1], get_formatted_value(value, number_of_digits))
        for key, value in consecutive_pages.items()
    }


def get_formatted_value(list, length):
    if len(list) <= 1:
        return ""
    size_with_padding = str(len(list)).zfill(length)
    first_page, *_, last_page = list
    return f"{size_with_padding}({first_page}-{last_page})"
