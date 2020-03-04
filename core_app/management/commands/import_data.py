from src.quran_srs import using_revision_data, expand_revision_data
from django.core.management.base import BaseCommand
from core_app.models import PageRevision, Student
import pytz


class Command(BaseCommand):
    help = "This downloads the data from Google sheets and inserts the data into Django's database"

    def add_arguments(self, parser):
        parser.add_argument("directory")
        # for optional arguments - flag
        parser.add_argument("--clean", action="store_true", default=False)

    def handle(self, *args, **options):
        if options["clean"]:
            PageRevision.objects.all().delete()

        with using_revision_data(options["directory"]) as data:
            student = Student.objects.all().first()

            rev_data = expand_revision_data(data)

            for page, rev_list in rev_data.items():
                for rev in rev_list:
                    date_with_timezone = pytz.utc.localize(rev["revision_date"])
                    PageRevision(
                        student=student,
                        page=int(page),
                        date=date_with_timezone,
                        word_mistakes=rev["word_mistakes"],
                        line_mistakes=rev["line_mistakes"],
                        current_interval=rev["current_interval"],
                    ).save()

            # pprint.pprint(rev_data)
