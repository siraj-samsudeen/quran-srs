from django.contrib import admin
from core_app.models import PageRevision, Student


class PageRevisionAdmin(admin.ModelAdmin):
    list_display = [
        "student",
        "page",
        "date",
        "word_mistakes",
        "line_mistakes",
        "current_interval",
    ]
    list_filter = ["page"]


class StudentAdmin(admin.ModelAdmin):
    list_display = ["id", "name"]


admin.site.register(PageRevision, PageRevisionAdmin)
admin.site.register(Student, StudentAdmin)
