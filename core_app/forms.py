from django import forms
from core_app.models import Student


class PageForm(forms.Form):
    page = forms.IntegerField(min_value=2, max_value=600)
    interval = forms.IntegerField()
    revision_count = forms.IntegerField(min_value=0)
    line_mistakes = forms.IntegerField(min_value=0, max_value=15)
    word_mistakes = forms.IntegerField(min_value=0)
    score = forms.IntegerField()


class RevisionEntryForm(forms.Form):
    line_mistakes = forms.IntegerField(min_value=0, max_value=15)
    word_mistakes = forms.IntegerField(min_value=0)


class RevisionIntervalForm(forms.Form):
    next_interval = forms.IntegerField()
    next_due_date = forms.DateField(disabled=True)
    line_mistakes = forms.IntegerField(widget=forms.HiddenInput())
    word_mistakes = forms.IntegerField(widget=forms.HiddenInput())
    sent = forms.BooleanField(widget=forms.HiddenInput())


class StudentForm(forms.ModelForm):
    class Meta:
        model = Student
        exclude = ["id", "account"]

