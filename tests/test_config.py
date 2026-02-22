from __future__ import annotations

import errno
import os
import unittest
from unittest.mock import patch

from app.config import load_settings


class SettingsRuntimeDefaultsTestCase(unittest.TestCase):
    def test_local_defaults_use_project_data_dir_and_scheduler(self) -> None:
        with patch.dict(os.environ, {}, clear=True):
            settings = load_settings(env_path=".env.missing")

        self.assertEqual(settings.db_path, "data/coffee_news.db")
        self.assertTrue(settings.scheduler_enabled)

    def test_vercel_defaults_use_tmp_and_scheduler_off(self) -> None:
        with patch.dict(os.environ, {"VERCEL": "1"}, clear=True):
            settings = load_settings(env_path=".env.missing")

        self.assertEqual(settings.db_path, "/tmp/coffee_news.db")
        self.assertFalse(settings.scheduler_enabled)

    def test_vercel_falls_back_to_tmp_when_db_path_is_read_only(self) -> None:
        with patch.dict(
            os.environ,
            {"VERCEL": "1", "DB_PATH": "data/coffee_news.db"},
            clear=True,
        ):
            with patch(
                "app.config.Path.mkdir",
                side_effect=[OSError(errno.EROFS, "Read-only file system"), None],
            ):
                settings = load_settings(env_path=".env.missing")

        self.assertEqual(settings.db_path, "/tmp/coffee_news.db")


if __name__ == "__main__":
    unittest.main()
