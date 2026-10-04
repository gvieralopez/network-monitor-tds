import re
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import timedelta
from enum import StrEnum

from pydantic import ValidationError
from pydantic.fields import FieldInfo

from network_monitor_tds.domain.plugins.models import JsonValue
from network_monitor_tds.plugins.sdk.models import PluginSettings

DURATION_PART = re.compile(r"(\d+)\s*([hms])")
UNIT_SECONDS = {"h": 3600, "m": 60, "s": 1}
DURATION_HINT = "Enter a duration such as 30s, 10m or 1h30m."
COMMON_HELP = {
    "interval": "How often the plugin runs.",
    "timeout": "Stops a run that takes longer than this.",
    "interface": "Network interface to use. Leave empty to use the one with the default route.",
}


class FieldKind(StrEnum):
    TEXT = "text"
    HIDDEN = "hidden"
    DURATION = "duration"
    TOGGLE = "toggle"
    NUMBER = "number"


@dataclass(frozen=True, slots=True)
class FormField:
    name: str
    label: str
    help: str
    kind: FieldKind
    value: str
    checked: bool
    error: str


@dataclass(frozen=True, slots=True)
class FormResult:
    settings: dict[str, JsonValue] | None
    errors: dict[str, str]


def parse_duration(text: str) -> timedelta | None:
    cleaned = text.strip().lower()
    if cleaned.isdigit():
        return timedelta(seconds=int(cleaned))
    parts = DURATION_PART.findall(cleaned)
    if not parts or DURATION_PART.sub("", cleaned).strip():
        return None
    return timedelta(seconds=sum(int(amount) * UNIT_SECONDS[unit] for amount, unit in parts))


def format_duration(value: timedelta) -> str:
    total = int(value.total_seconds())
    hours, rest = divmod(total, 3600)
    minutes, seconds = divmod(rest, 60)
    parts = [f"{amount}{unit}" for amount, unit in ((hours, "h"), (minutes, "m"), (seconds, "s"))]
    return "".join(part for part in parts if not part.startswith("0")) or "0s"


def settings_fields(
    model: type[PluginSettings], settings: Mapping[str, JsonValue], errors: Mapping[str, str]
) -> tuple[FormField, ...]:
    current = _current(model, settings)
    return tuple(
        _form_field(name, field, getattr(current, name), errors.get(name, ""))
        for name, field in model.model_fields.items()
    )


def read_settings_form(
    model: type[PluginSettings], form: Mapping[str, str], settings: Mapping[str, JsonValue]
) -> FormResult:
    values: dict[str, object] = {}
    errors: dict[str, str] = {}
    for name, field in model.model_fields.items():
        match _kind(field):
            case FieldKind.TOGGLE:
                values[name] = name in form
            case FieldKind.DURATION:
                duration = parse_duration(form.get(name, ""))
                if duration is None:
                    errors[name] = DURATION_HINT
                values[name] = duration or field.default
            case FieldKind.HIDDEN:
                values[name] = form.get(name) or settings.get(name, "")
            case _:
                values[name] = form.get(name, "")
    try:
        validated = model.model_validate(values)
    except ValidationError as error:
        return FormResult(settings=None, errors=_field_errors(error) | errors)
    if errors:
        return FormResult(settings=None, errors=errors)
    return FormResult(settings=validated.model_dump(mode="json"), errors={})


def _current(model: type[PluginSettings], settings: Mapping[str, JsonValue]) -> PluginSettings:
    try:
        return model.model_validate(settings)
    except ValidationError:
        return model()


def _form_field(name: str, field: FieldInfo, value: object, error: str) -> FormField:
    kind = _kind(field)
    return FormField(
        name=name,
        label=field.title or name.replace("_", " ").capitalize(),
        help=field.description or COMMON_HELP.get(name, ""),
        kind=kind,
        value=_display(kind, value),
        checked=kind is FieldKind.TOGGLE and bool(value),
        error=error,
    )


def _kind(field: FieldInfo) -> FieldKind:
    if field.annotation is timedelta:
        return FieldKind.DURATION
    if field.annotation is bool:
        return FieldKind.TOGGLE
    if field.annotation in (int, float):
        return FieldKind.NUMBER
    if not field.repr:
        return FieldKind.HIDDEN
    return FieldKind.TEXT


def _display(kind: FieldKind, value: object) -> str:
    if kind is FieldKind.HIDDEN:
        return ""
    if isinstance(value, timedelta):
        return format_duration(value)
    return "" if isinstance(value, bool) else str(value)


def _field_errors(error: ValidationError) -> dict[str, str]:
    return {
        str(detail["loc"][0]) if detail["loc"] else "": detail["msg"].removeprefix("Value error, ")
        for detail in error.errors()
    }
