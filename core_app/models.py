import datetime

from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.contrib.auth.models import User


class Student(models.Model):
    name = models.CharField(max_length=64)
    account = models.ForeignKey(User, on_delete=models.CASCADE)

    def __str__(self):
        return self.name


class PageRevision(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE)

    page = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(606)]
    )
    date = models.DateTimeField(default=datetime.datetime.utcnow)
    word_mistakes = models.PositiveSmallIntegerField(default=0)
    line_mistakes = models.PositiveSmallIntegerField(default=0)
    current_interval = models.SmallIntegerField(default=0)
