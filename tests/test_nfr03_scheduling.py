"""Tests for NFR-03 daily backup scheduling."""

import pytest

from scripts.schedule_daily_backup import (
    CRON_MARKER,
    build_cron_entry,
    remove_managed_entry,
    replace_managed_entry,
    validate_time,
)


def test_schedule_defaults_to_two_am(tmp_path):
    """Verify the default schedule runs at 02:00."""

    entry = build_cron_entry(
        project_root=tmp_path,
        python_executable="/usr/bin/python3",
    )

    assert entry.startswith("0 2 * * * ")
    assert CRON_MARKER in entry


def test_schedule_uses_requested_time(tmp_path):
    """Verify that the requested daily time is used."""

    entry = build_cron_entry(
        project_root=tmp_path,
        python_executable="/usr/bin/python3",
        schedule_time="04:30",
    )

    assert entry.startswith("30 4 * * * ")


@pytest.mark.parametrize(
    "invalid_time",
    [
        "25:00",
        "12:60",
        "abc",
        "2",
        "02:00:00",
        "",
    ],
)
def test_invalid_schedule_time_is_rejected(invalid_time):
    """Verify that invalid scheduling times are rejected."""

    with pytest.raises(ValueError):
        validate_time(invalid_time)


def test_replacing_schedule_preserves_unrelated_jobs():
    """Verify that installing a job preserves other cron entries."""

    existing = (
        "15 1 * * * /usr/bin/cleanup\n"
        f"0 3 * * * /old/backup {CRON_MARKER}\n"
        "30 5 * * * /usr/bin/report\n"
    )

    replacement = (
        f"0 2 * * * /new/backup {CRON_MARKER}"
    )

    updated = replace_managed_entry(existing, replacement)

    assert "/usr/bin/cleanup" in updated
    assert "/usr/bin/report" in updated
    assert "/old/backup" not in updated
    assert "/new/backup" in updated
    assert updated.count(CRON_MARKER) == 1


def test_removing_schedule_preserves_unrelated_jobs():
    """Verify that removing the job preserves other cron entries."""

    existing = (
        "15 1 * * * /usr/bin/cleanup\n"
        f"0 2 * * * /backup {CRON_MARKER}\n"
    )

    updated = remove_managed_entry(existing)

    assert "/usr/bin/cleanup" in updated
    assert CRON_MARKER not in updated


def test_removing_schedule_without_managed_job_is_safe():
    """Verify that unrelated crontab content remains unchanged."""

    existing = "15 1 * * * /usr/bin/cleanup\n"

    assert remove_managed_entry(existing) == existing