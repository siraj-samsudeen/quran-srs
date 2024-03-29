from django import forms

from core_app.models import Student


class RevisionEntryForm(forms.Form):
    word_mistakes = forms.IntegerField(min_value=0, required=False, initial=0)
    line_mistakes = forms.IntegerField(min_value=0, max_value=15, required=False)

    CHOICES = [
        ("e", "Easy"),
        ("o", "OK"),
        ("h", "Hard"),
    ]

    difficulty_level = forms.ChoiceField(choices=CHOICES, widget=forms.RadioSelect, initial="o")


class BulkUpdateForm(forms.Form):
    from_page = forms.IntegerField(min_value=0, max_value=604, required=True)
    to_page = forms.IntegerField(min_value=0, max_value=604, required=True)
    word_mistakes = forms.IntegerField(min_value=0, required=False)
    line_mistakes = forms.IntegerField(min_value=0, max_value=15, required=False)

    CHOICES = [
        ("e", "Easy"),
        ("o", "OK"),
        ("h", "Hard"),
    ]

    difficulty_level = forms.ChoiceField(choices=CHOICES, widget=forms.RadioSelect, initial="o")


class StudentForm(forms.ModelForm):
    class Meta:
        model = Student
        exclude = ["id", "account"]
