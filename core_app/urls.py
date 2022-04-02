from django.contrib.auth.views import LoginView, LogoutView
from django.urls import path

from . import views

urlpatterns = [
    path("accounts/login/", LoginView.as_view(template_name="login.html"), name="login"),
    path("accounts/logout/", LogoutView.as_view(next_page="/accounts/login/"), name="logout"),
    path("", views.home, name="home"),
    path("student/<int:student_id>/all/", views.page_all, name="page_all"),
    path("student/<int:student_id>/due/", views.page_due, name="page_due"),
    path(
        "student/<int:student_id>/page/<int:page>/<int:due_page>/",
        views.page_entry,
        name="page_entry",
    ),
    path("student/<int:student_id>/new/", views.page_new, name="page_new"),
    path("student/<int:student_id>/bulk_update/", views.bulk_update, name="bulk_update"),
]
