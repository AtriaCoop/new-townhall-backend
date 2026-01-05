from django.test import TestCase
from django.core.management import call_command
from django.utils import timezone

from users.types import CreateReportData
from users.services import ReportServices
from datetime import datetime


class TestReportService(TestCase):
    def setUp(self):
        call_command("loaddata", "fixtures/user_fixture.json", verbosity=0)
        call_command("loaddata", "fixtures/report_fixture.json", verbosity=0)

    def test_create_report_success(self):
        # Arrange
        create_report_data = CreateReportData(
            user_id=1,
            content="There is a bug here. Fix it!",
            created_at=timezone.make_aware(datetime(2025, 11, 22, 10, 0)),
        )

        # Act
        report = ReportServices.create_report(create_report_data)

        # Assert
        assert report.user_id == 1
        assert report.content == "There is a bug here. Fix it!"
        assert report.created_at == timezone.make_aware(datetime(2025, 11, 22, 10, 0))
