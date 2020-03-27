from django.contrib import admin
from core_app.models import PageRevision, Student


class PageRevisionAdmin(admin.ModelAdmin):
    # TODO How to exclude
    list_display = [
        "date",
        "student",
        "page",
        "word_mistakes",
        "line_mistakes",
        "current_interval",
        "difficulty_level",
    ]
    list_filter = ["student", "date", "page"]


class StudentAdmin(admin.ModelAdmin):
    list_display = ["id", "name"]


admin.site.register(PageRevision, PageRevisionAdmin)
admin.site.register(Student, StudentAdmin)
