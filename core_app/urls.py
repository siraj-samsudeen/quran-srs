"""project URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
import core_app.views as view
from django.contrib.auth.views import LoginView, LogoutView

from rest_framework import routers


router = routers.DefaultRouter()
router.register("students", view.StudentViewSet)


urlpatterns = [
    path("api/students/last/", view.last_student),
    path("api/", include(router.urls)),
    path("accounts/login/", LoginView.as_view(template_name="admin/login.html")),
    path("accounts/logout/", LogoutView.as_view(), name="logout"),
    path("", view.home, name="home"),
    path("student/<int:student_id>/all/", view.page_all, name="page_all"),
    path(
        "student/<int:student_id>/page/<int:page>/revision/",
        view.page_revision,
        name="page_revision",
    ),
    path("student/<int:student_id>/due/", view.page_due, name="page_due"),
    path(
        "student/<int:student_id>/page/<int:page>/<int:due_page>/",
        view.page_entry,
        name="page_entry",
    ),
    path("student/<int:student_id>/new/", view.page_new, name="page_new"),
    path("student/<int:student_id>/revise/", view.page_revise, name="pages_to_revise"),
]
