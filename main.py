from fasthtml.common import *
from app.users_controller import users_app
from app.revision_controller import revision_app
from app.new_memorization import new_memorization_app
from app.admin_controller import admin_app
from app.page_details_controller import page_details_app
from app.profile_controller import profile_app
from app.hafiz_controller import hafiz_app
from app.home_controller import home_app
from app.common_function import create_app_with_auth

app, rt = create_app_with_auth(
    routes=[
        Mount("/users", users_app, name="users"),
        Mount("/revision", revision_app, name="revision"),
        Mount("/new_memorization", new_memorization_app, name="new_memorization"),
        Mount("/admin", admin_app, name="admin"),
        Mount("/page_details", page_details_app, name="page_details"),
        Mount("/profile", profile_app, name="profile"),
        Mount("/hafiz", hafiz_app, name="hafiz"),
        Mount("/", home_app, name="home"),
    ]
)

print("-" * 15, "ROUTES=", app.routes)

serve()
