from datetime import UTC, datetime

from app.api.v1.util.util import time_passed


def test_func_time_passad_true():
    created_at = datetime(2026, 5, 9, 10, 0, tzinfo=UTC)

    assert time_passed(created_at) is True


def test_func_time_passad_false():
    created_at = datetime(2026, 5, 10, 10, 0, tzinfo=UTC)

    assert time_passed(created_at) is False
