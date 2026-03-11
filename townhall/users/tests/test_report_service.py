from django.test import TestCase
from django.core.management import call_command
from django.utils import timezone
from django.core.exceptions import ValidationError

from users.types import CreateReportData
from users.services import ReportServices
from users.models import Report
from datetime import datetime
from unittest.mock import patch


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

    def test_get_report_success(self):
        # Act
        report = ReportServices.get_report(id=1)

        # Assert
        assert report.id == 1
        assert (
            report.created_at.strftime("%Y-%m-%dT%H:%M:%SZ") == "2025-11-22T12:00:00Z"
        )
        assert report.user_id == 1

    @patch("users.daos.ReportDao.get_report")
    def test_get_report_failed_not_found(self, mock_get_report):
        # Arrange
        mock_get_report.side_effect = Report.DoesNotExist
        report_id = -2  # Assuming this ID does not exist

        # Act & Assert
        with self.assertRaises(ValidationError) as context:
            ReportServices.get_report(report_id)

        # Assert
        assert (
            str(context.exception)
            == f"['Report with the given id: {report_id}, does not exist.']"
        )
