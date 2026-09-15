"""Explicit private config regression. Synthetic credentials and no SMTP network."""
import contextlib
import io
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from app import create_app
from config import get_config


class MailConfigTests(unittest.TestCase):
    def test_explicit_file_reaches_factory_and_environment_wins(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'private.env'
            path.write_text('MAIL_ENABLED=true\nMAIL_BACKEND=smtp\nSMTP_HOST=smtp.example.test\nSMTP_PORT=587\nSMTP_USE_TLS=true\nSMTP_USE_SSL=false\nSMTP_USERNAME=test-login\nSMTP_PASSWORD="synthetic-secret"\nMAIL_FROM_ADDRESS=sender@example.test\nEMAIL_VERIFICATION_ENABLED=true\nACCOUNT_RECOVERY_ENABLED=false\nORDER_EMAIL_NOTIFICATIONS_ENABLED=false\n')
            with patch.dict(os.environ, {'YOLI_ENV_FILE': str(path), 'SMTP_PORT': '2525'}, clear=True):
                output = io.StringIO()
                with contextlib.redirect_stdout(output), contextlib.redirect_stderr(output):
                    app = create_app({'SECRET_KEY': 'test', 'SQLALCHEMY_DATABASE_URI': 'sqlite://'})
                    status = app.test_cli_runner().invoke(args=['mail-status'])
                self.assertEqual(status.exit_code, 0)
                self.assertEqual(app.config['SMTP_PORT'], 2525)
                self.assertEqual(app.config['SMTP_HOST'], 'smtp.example.test')
                self.assertEqual(app.config['MAIL_BACKEND'], 'smtp')
                self.assertTrue(app.config['MAIL_ENABLED'])
                self.assertTrue(app.config['EMAIL_VERIFICATION_ENABLED'])
                self.assertFalse(app.config['ACCOUNT_RECOVERY_ENABLED'])
                self.assertFalse(app.config['ORDER_EMAIL_NOTIFICATIONS_ENABLED'])
                self.assertIn('SMTP_PASSWORD_PRESENT=True', status.output)
                for private in ('synthetic-secret', 'test-login', 'sender@example.test'):
                    self.assertNotIn(private, output.getvalue() + status.output)

    def test_missing_explicit_file_fails_instead_of_silent_defaults(self):
        with patch.dict(os.environ, {'YOLI_ENV_FILE': '/nonexistent/private.env'}, clear=True):
            with self.assertRaisesRegex(RuntimeError, 'archivo de entorno'):
                get_config()
