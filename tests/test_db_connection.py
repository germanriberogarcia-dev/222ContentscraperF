from __future__ import annotations

import errno
import sqlite3
import unittest
from unittest.mock import patch

from app import db


class DbConnectionFallbackTestCase(unittest.TestCase):
    def test_falls_back_to_tmp_on_read_only_data_dir(self) -> None:
        # First mkdir call is for configured path (fails read-only), second is for /tmp (succeeds).
        with patch(
            "app.db.Path.mkdir",
            side_effect=[OSError(errno.EROFS, "Read-only file system"), None],
        ):
            with patch("app.db.sqlite3.connect", return_value=sqlite3.connect(":memory:")) as connect_mock:
                with db.connection("data/coffee_news.db") as conn:
                    value = conn.execute("SELECT 1").fetchone()[0]

        self.assertEqual(value, 1)
        self.assertEqual(connect_mock.call_args.args[0], "/tmp/coffee_news.db")

    def test_falls_back_to_tmp_when_sqlite_open_fails(self) -> None:
        with patch("app.db.Path.mkdir", return_value=None):
            with patch(
                "app.db.sqlite3.connect",
                side_effect=[sqlite3.OperationalError("unable to open database file"), sqlite3.connect(":memory:")],
            ) as connect_mock:
                with db.connection("data/coffee_news.db") as conn:
                    value = conn.execute("SELECT 1").fetchone()[0]

        self.assertEqual(value, 1)
        self.assertEqual(connect_mock.call_args.args[0], "/tmp/coffee_news.db")


if __name__ == "__main__":
    unittest.main()
