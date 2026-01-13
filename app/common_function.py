from fasthtml.common import *
from app.middleware import (
    user_auth, user_bware, hafiz_auth, hafiz_bware, create_app_with_auth,
    daisyui_css, tabulator_css, tabulator_js, style_css, favicon, hyperscript_header, alpinejs_header
)
from app.common_view import (
    error_toast, success_toast, warning_toast, main_area, get_page_description,
    group_by_type, render_rating, rating_dropdown, rating_radio, create_count_link,
    render_rep_config_form, render_mode_dropdown, render_progress_cell,
    render_graduate_cell, render_inline_mode_config, render_mode_and_reps,
    render_surah_header, render_bulk_checkbox, render_page_number_cell, render_start_text_cell
)
from app.common_model import (
    get_current_date, get_hafizs_items, get_mode_count, get_actual_interval,
    get_planned_next_interval, add_revision_record, get_not_memorized_records,
    get_last_added_full_cycle_page, find_next_memorized_item_id,
    populate_hafizs_items_stat_columns, get_current_plan_id, get_full_review_item_ids,
    get_juz_number_for_item, get_unmemorized_items, get_mode_specific_hafizs_items,
    get_datewise_revisions, get_earliest_revision_date, get_unrevised_memorized_items,
    get_prev_next_item_ids, get_item_page_portion, get_page_count, get_surah_name,
    get_page_number, get_mode_name, get_mode_icon, can_graduate, get_last_item_id,
    get_juz_name, get_mode_name_and_code, get_page_part_info, get_status,
    get_status_display, get_status_counts
)
# Re-export home view functions for backward compatibility
from app.home_view import (
    render_range_row, render_bulk_action_bar, render_summary_table,
    make_summary_table, render_current_date, MODE_PREDICATES, should_include_in_daily_reps,
    should_include_in_weekly_reps, should_include_in_fortnightly_reps, should_include_in_monthly_reps,
    should_include_in_srs, should_include_in_full_cycle, _is_review_due, _is_reviewed_today,
    _has_memorized, _has_revisions_in_mode, _has_revisions_today_in_mode, _was_newly_memorized_today,
    _create_standard_rep_mode_predicate, get_mode_condition, row_background_color
)
