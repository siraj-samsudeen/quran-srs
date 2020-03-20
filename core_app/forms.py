from django import forms
from core_app.models import Student


class RevisionEntryForm(forms.Form):
    word_mistakes = forms.IntegerField(min_value=0, required=False)
    line_mistakes = forms.IntegerField(min_value=0, max_value=15, required=False)


class StudentForm(forms.ModelForm):
    class Meta:
        model = Student
        exclude = ["id", "account"]
