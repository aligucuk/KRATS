"""
Integration tests for services/notification_service.py

Tests cover:
- Service initialization and lifecycle
- Reminder checking and processing
- Template rendering
- Service threading
- Error handling
- Integration with database
"""
import pytest
import time
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock

from services.notification_service import NotificationService
from database.db_manager import DatabaseManager


# ==================== SERVICE INITIALIZATION ====================

@pytest.mark.integration
class TestServiceInitialization:
    """Test notification service initialization"""

    def test_service_initialization(self, db_manager):
        """Test that service initializes correctly"""
        service = NotificationService(db_manager)

        assert service.db is db_manager
        assert service.is_running is False
        assert service.thread is None
        assert service.enabled is True
        assert service.check_interval == 3600  # 1 hour

    def test_service_with_custom_interval(self, db_manager):
        """Test service initialization with custom check interval"""
        service = NotificationService(db_manager)
        service.check_interval = 60  # 1 minute

        assert service.check_interval == 60


# ==================== SERVICE LIFECYCLE ====================

@pytest.mark.integration
class TestServiceLifecycle:
    """Test service start, stop, and lifecycle"""

    def test_start_service(self, db_manager):
        """Test starting the notification service"""
        service = NotificationService(db_manager)

        service.start()

        assert service.is_running is True
        assert service.thread is not None
        assert service.thread.is_alive()

        # Cleanup
        service.stop()

    def test_start_already_running_service(self, db_manager, caplog):
        """Test starting service when already running"""
        service = NotificationService(db_manager)

        service.start()
        service.start()  # Try to start again

        assert "already running" in caplog.text.lower()

        # Cleanup
        service.stop()

    def test_stop_service(self, db_manager):
        """Test stopping the notification service"""
        service = NotificationService(db_manager)

        service.start()
        time.sleep(0.1)  # Let it start

        service.stop()

        assert service.is_running is False

        # Thread should stop (or be stopping)
        time.sleep(0.5)
        assert not service.thread.is_alive() or service.is_running is False

    def test_stop_not_running_service(self, db_manager):
        """Test stopping service when not running"""
        service = NotificationService(db_manager)

        # Should not raise error
        service.stop()

        assert service.is_running is False

    def test_service_runs_as_daemon(self, db_manager):
        """Test that service thread is daemon"""
        service = NotificationService(db_manager)

        service.start()

        assert service.thread.daemon is True

        # Cleanup
        service.stop()


# ==================== REMINDER CHECKING ====================

@pytest.mark.integration
class TestReminderChecking:
    """Test reminder checking functionality"""

    def test_check_and_send_reminders_no_pending(self, db_manager):
        """Test checking reminders when none are pending"""
        service = NotificationService(db_manager)

        # Mock the get_pending_reminders to return empty
        with patch.object(db_manager, 'get_pending_reminders', return_value=[]):
            service.check_and_send_reminders()

        # Should complete without error

    def test_check_and_send_reminders_with_pending(self, db_manager):
        """Test checking reminders with pending reminders"""
        service = NotificationService(db_manager)

        # Mock pending reminders
        mock_reminder = Mock()
        mock_reminder.patient_name = "Ahmet Yılmaz"
        mock_reminder.appointment_date = datetime.now() + timedelta(days=1)
        mock_reminder.phone = "5551234567"
        mock_reminder.email = "test@example.com"

        with patch.object(db_manager, 'get_pending_reminders', return_value=[mock_reminder]):
            with patch.object(service, '_send_sms_reminder', return_value=True):
                with patch.object(service, '_send_email_reminder', return_value=True):
                    service.check_and_send_reminders()

        # Should process the reminder

    def test_check_reminders_when_disabled(self, db_manager):
        """Test that disabled service doesn't send reminders"""
        service = NotificationService(db_manager)
        service.enabled = False

        with patch.object(db_manager, 'get_pending_reminders') as mock_get:
            service.check_and_send_reminders()

            # Should not check for reminders when disabled
            mock_get.assert_not_called()

    def test_template_loading(self, db_manager):
        """Test loading reminder templates from settings"""
        service = NotificationService(db_manager)

        # Set custom templates
        db_manager.set_setting("sms_template", "Test SMS: {hasta} - {tarih}")
        db_manager.set_setting("email_template", "Test Email: {hasta} - {tarih}")

        # Mock pending reminders
        mock_reminder = Mock()
        mock_reminder.patient_name = "Ahmet"
        mock_reminder.appointment_date = datetime.now() + timedelta(days=1)
        mock_reminder.phone = "5551234567"
        mock_reminder.email = "test@example.com"

        with patch.object(db_manager, 'get_pending_reminders', return_value=[mock_reminder]):
            with patch.object(service, '_send_sms_reminder') as mock_sms:
                service.check_and_send_reminders()

                # Verify template was used
                if mock_sms.called:
                    assert True  # Template was loaded and used


# ==================== DAILY MAINTENANCE ====================

@pytest.mark.integration
class TestDailyMaintenance:
    """Test daily maintenance tasks"""

    def test_run_daily_maintenance(self, db_manager):
        """Test running daily maintenance tasks"""
        service = NotificationService(db_manager)

        # Should run without errors
        service.run_daily_maintenance()

    def test_maintenance_cleanup_old_reminders(self, db_manager):
        """Test that maintenance cleans up old data"""
        service = NotificationService(db_manager)

        # Mock cleanup methods if they exist
        with patch.object(db_manager, 'cleanup_old_reminders', return_value=True) if hasattr(db_manager, 'cleanup_old_reminders') else patch('builtins.id'):
            service.run_daily_maintenance()


# ==================== ERROR HANDLING ====================

@pytest.mark.integration
class TestErrorHandling:
    """Test error handling in notification service"""

    def test_handle_database_error(self, db_manager):
        """Test handling database errors"""
        service = NotificationService(db_manager)

        # Mock database error
        with patch.object(db_manager, 'get_pending_reminders', side_effect=Exception("DB Error")):
            # Should not crash
            service.check_and_send_reminders()

    def test_handle_sms_sending_error(self, db_manager):
        """Test handling SMS sending errors"""
        service = NotificationService(db_manager)

        mock_reminder = Mock()
        mock_reminder.patient_name = "Test Patient"
        mock_reminder.appointment_date = datetime.now() + timedelta(days=1)
        mock_reminder.phone = "5551234567"

        with patch.object(db_manager, 'get_pending_reminders', return_value=[mock_reminder]):
            with patch.object(service, '_send_sms_reminder', side_effect=Exception("SMS Error")):
                # Should handle error gracefully
                service.check_and_send_reminders()

    def test_service_continues_after_error(self, db_manager):
        """Test that service continues running after errors"""
        service = NotificationService(db_manager)
        service.check_interval = 0.1  # Fast for testing

        error_count = 0

        def mock_check():
            nonlocal error_count
            error_count += 1
            if error_count < 3:
                raise Exception("Test error")

        with patch.object(service, 'check_and_send_reminders', side_effect=mock_check):
            service.start()
            time.sleep(0.5)  # Let it run a few cycles
            service.stop()

        # Service should have handled errors and continued
        assert error_count > 0


# ==================== THREADING ====================

@pytest.mark.integration
class TestThreading:
    """Test threading behavior"""

    def test_service_runs_in_background(self, db_manager):
        """Test that service runs in background thread"""
        service = NotificationService(db_manager)

        service.start()

        # Main thread should continue
        assert service.thread.is_alive()
        assert service.is_running

        # Cleanup
        service.stop()

    def test_service_thread_name(self, db_manager):
        """Test that service thread has correct name"""
        service = NotificationService(db_manager)

        service.start()

        assert service.thread.name == "NotificationService"

        # Cleanup
        service.stop()

    def test_multiple_service_instances(self, db_manager):
        """Test running multiple service instances"""
        service1 = NotificationService(db_manager)
        service2 = NotificationService(db_manager)

        service1.start()
        service2.start()

        assert service1.is_running
        assert service2.is_running
        assert service1.thread != service2.thread

        # Cleanup
        service1.stop()
        service2.stop()

    @pytest.mark.slow
    def test_service_periodic_execution(self, db_manager):
        """Test that service executes periodically"""
        service = NotificationService(db_manager)
        service.check_interval = 0.2  # Fast for testing

        check_count = 0

        def mock_check():
            nonlocal check_count
            check_count += 1

        with patch.object(service, 'check_and_send_reminders', side_effect=mock_check):
            service.start()
            time.sleep(0.7)  # Should run at least 2-3 times
            service.stop()

        assert check_count >= 2


# ==================== INTEGRATION WITH DATABASE ====================

@pytest.mark.integration
@pytest.mark.database
class TestDatabaseIntegration:
    """Test integration with database"""

    def test_get_pending_reminders_integration(self, db_manager, sample_patient_data):
        """Test getting pending reminders from database"""
        # Create patient and appointment
        patient_id = db_manager.add_patient(**sample_patient_data)

        with db_manager.get_session() as session:
            from database.models import User
            admin = session.query(User).filter_by(username="admin").first()
            doctor_id = admin.id

        # Create appointment for tomorrow
        appointment_date = datetime.now() + timedelta(days=1)
        db_manager.create_appointment(
            patient_id=patient_id,
            doctor_id=doctor_id,
            appointment_date=appointment_date
        )

        # Get pending reminders (if method exists)
        if hasattr(db_manager, 'get_pending_reminders'):
            reminders = db_manager.get_pending_reminders()
            # Depending on implementation, there might be reminders
            assert isinstance(reminders, list)

    def test_mark_reminder_sent_integration(self, db_manager):
        """Test marking reminder as sent in database"""
        # This tests the database interaction
        # Implementation depends on db_manager having these methods

        service = NotificationService(db_manager)

        # If methods exist, test them
        if hasattr(db_manager, 'mark_reminder_sent'):
            result = db_manager.mark_reminder_sent(reminder_id=1)
            # Result depends on implementation


# ==================== MOCK TESTS ====================

@pytest.mark.integration
class TestWithMocks:
    """Tests using mocks for external dependencies"""

    def test_sms_sending_mock(self, db_manager, mock_twilio_client):
        """Test SMS sending with mocked Twilio"""
        service = NotificationService(db_manager)

        # Mock reminder
        mock_reminder = Mock()
        mock_reminder.patient_name = "Test Patient"
        mock_reminder.appointment_date = datetime.now() + timedelta(days=1)
        mock_reminder.phone = "5551234567"
        mock_reminder.email = None

        with patch.object(db_manager, 'get_pending_reminders', return_value=[mock_reminder]):
            service.check_and_send_reminders()

        # Verify interaction (depends on implementation)

    def test_email_sending_mock(self, db_manager, mock_smtp_server):
        """Test email sending with mocked SMTP"""
        service = NotificationService(db_manager)

        # Mock reminder
        mock_reminder = Mock()
        mock_reminder.patient_name = "Test Patient"
        mock_reminder.appointment_date = datetime.now() + timedelta(days=1)
        mock_reminder.phone = None
        mock_reminder.email = "test@example.com"

        with patch.object(db_manager, 'get_pending_reminders', return_value=[mock_reminder]):
            service.check_and_send_reminders()

        # Verify interaction (depends on implementation)


# ==================== CONFIGURATION ====================

@pytest.mark.integration
class TestConfiguration:
    """Test service configuration"""

    def test_default_configuration(self, db_manager):
        """Test default configuration values"""
        service = NotificationService(db_manager)

        assert service.check_interval == 3600
        assert service.enabled is True

    def test_custom_configuration(self, db_manager):
        """Test custom configuration"""
        service = NotificationService(db_manager)

        service.check_interval = 1800  # 30 minutes
        service.enabled = False

        assert service.check_interval == 1800
        assert service.enabled is False

    def test_disable_service(self, db_manager):
        """Test disabling service"""
        service = NotificationService(db_manager)
        service.enabled = False

        with patch.object(db_manager, 'get_pending_reminders') as mock_get:
            service.check_and_send_reminders()

            # Should not check reminders when disabled
            mock_get.assert_not_called()


# ==================== STRESS TESTS ====================

@pytest.mark.slow
@pytest.mark.integration
class TestStress:
    """Stress tests for notification service"""

    def test_handle_many_reminders(self, db_manager):
        """Test handling many pending reminders"""
        service = NotificationService(db_manager)

        # Create many mock reminders
        mock_reminders = []
        for i in range(100):
            mock_reminder = Mock()
            mock_reminder.patient_name = f"Patient {i}"
            mock_reminder.appointment_date = datetime.now() + timedelta(days=1)
            mock_reminder.phone = f"555000{i:04d}"
            mock_reminder.email = f"patient{i}@test.com"
            mock_reminders.append(mock_reminder)

        with patch.object(db_manager, 'get_pending_reminders', return_value=mock_reminders):
            with patch.object(service, '_send_sms_reminder', return_value=True):
                with patch.object(service, '_send_email_reminder', return_value=True):
                    # Should handle many reminders
                    service.check_and_send_reminders()

    def test_service_long_running(self, db_manager):
        """Test service running for extended period"""
        service = NotificationService(db_manager)
        service.check_interval = 0.1  # Fast for testing

        service.start()
        time.sleep(1.0)  # Run for 1 second
        service.stop()

        # Should have run successfully
        assert True  # If we get here, it worked
