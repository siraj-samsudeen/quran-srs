from fasthtml.common import *
from app.common_function import create_app_with_auth
from app.page_details_model import (
    get_page_details_summary, 
    get_item_details,
    is_item_active
)
from app.page_details_view import (
    render_page_details_table, 
    render_page_level_details, 
    render_page_description_edit_form
)

page_details_app, rt = create_app_with_auth()

@page_details_app.get("/")
def page_details_view(auth):
    summary_data = get_page_details_summary(auth)
    return render_page_details_table(summary_data, auth)

@page_details_app.get("/{item_id}")
def display_page_level_details(auth, item_id: int):
    # Prevent editing description for inactive items
    is_active = is_item_active(item_id)
    return render_page_level_details(auth, item_id, is_active)

@page_details_app.get("/edit/{item_id}")
def page_description_edit_form(item_id: int):
    item_details = get_item_details(item_id)
    return render_page_description_edit_form(item_id, item_details)