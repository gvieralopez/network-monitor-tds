from collections.abc import Mapping
from datetime import timedelta

import pytest
from pydantic import Field

from network_monitor_tds.plugins.sdk.models import PluginSettings
from network_monitor_tds.web.forms import (
    DURATION_HINT,
    FieldKind,
    FormField,
    format_duration,
    parse_duration,
    read_settings_form,
    settings_fields,
)


class Sample(PluginSettings):
    interval: timedelta = timedelta(minutes=5)
    url: str = Field(default="", title="Server address", description="Where it lives")
    token: str = Field(default="", repr=False)
    verify: bool = True
    retries: int = 3

    @classmethod
    def placeholders(cls) -> Mapping[str, str]:
        return {"url": "dns.lan"}


@pytest.mark.parametrize(
    ("text", "duration"),
    [
        ("30s", timedelta(seconds=30)),
        ("5m", timedelta(minutes=5)),
        ("1h30m", timedelta(hours=1, minutes=30)),
        (" 1h 5m 3s ", timedelta(hours=1, minutes=5, seconds=3)),
        ("90", timedelta(seconds=90)),
        ("5M", timedelta(minutes=5)),
        ("", None),
        ("soon", None),
        ("5x", None),
        ("5m soon", None),
    ],
)
def test_parse_duration(text: str, duration: timedelta | None) -> None:
    assert parse_duration(text) == duration


@pytest.mark.parametrize(
    ("duration", "text"),
    [
        (timedelta(), "0s"),
        (timedelta(seconds=45), "45s"),
        (timedelta(minutes=5), "5m"),
        (timedelta(seconds=90), "1m30s"),
        (timedelta(hours=2, seconds=5), "2h5s"),
    ],
)
def test_format_duration(duration: timedelta, text: str) -> None:
    assert format_duration(duration) == text


def test_settings_fields_describe_each_setting() -> None:
    fields = settings_fields(Sample, {"url": "http://dns", "token": "s3cret"}, {"url": "Bad"})

    assert fields == (
        FormField("interval", "Run every", "How often it runs.", FieldKind.DURATION, "5m", "", False, ""),
        FormField("url", "Server address", "Where it lives", FieldKind.TEXT, "http://dns", "dns.lan", False, "Bad"),
        FormField("token", "Token", "", FieldKind.HIDDEN, "", "Saved, leave empty to keep", False, ""),
        FormField("verify", "Verify", "", FieldKind.TOGGLE, "", "", True, ""),
        FormField("retries", "Retries", "", FieldKind.NUMBER, "3", "", False, ""),
    )  # fmt: skip


def test_settings_fields_fall_back_to_defaults_for_invalid_settings() -> None:
    fields = settings_fields(Sample, {"interval": "soon"}, {})

    assert fields[0].value == "5m"


def test_read_settings_form() -> None:
    result = read_settings_form(
        Sample, {"interval": "10m", "url": "http://dns", "retries": "4"}, {"token": "s3cret"}
    )

    assert result.errors == {}
    assert result.settings == {
        "interval": "PT10M",
        "url": "http://dns",
        "token": "s3cret",
        "verify": False,
        "retries": 4,
    }


def test_read_settings_form_replaces_secret_when_given() -> None:
    result = read_settings_form(
        Sample, {"interval": "5m", "token": "new", "retries": "1"}, {"token": "old"}
    )

    assert result.settings is not None
    assert result.settings["token"] == "new"


def test_read_settings_form_reports_every_error() -> None:
    result = read_settings_form(Sample, {"interval": "soon", "retries": "many"}, {})

    assert result.settings is None
    assert result.errors["interval"] == DURATION_HINT
    assert "integer" in result.errors["retries"]


def test_secret_field_says_when_nothing_is_saved() -> None:
    token = next(field for field in settings_fields(Sample, {}, {}) if field.name == "token")

    assert token.placeholder == "Not set"
