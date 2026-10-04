import pytest
from pydantic import ValidationError

from network_monitor_tds.domain.devices.models import Category, DeviceLabels
from network_monitor_tds.web.pages.schemas import LabelsForm


@pytest.mark.parametrize(
    ("data", "labels"),
    [
        ({}, DeviceLabels(None, None, None)),
        ({"name": "  ", "category": "", "icon": ""}, DeviceLabels(None, None, None)),
        (
            {"name": " Garden sensor ", "category": "iot", "icon": "bulb"},
            DeviceLabels("Garden sensor", Category.IOT, "bulb"),
        ),
    ],
)
def test_labels_form(data: dict[str, str], labels: DeviceLabels) -> None:
    assert LabelsForm.model_validate(data).to_labels() == labels


@pytest.mark.parametrize(
    "data", [{"icon": "rocket"}, {"category": "spaceship"}, {"surprise": "field"}]
)
def test_labels_form_rejects_invalid_input(data: dict[str, str]) -> None:
    with pytest.raises(ValidationError):
        LabelsForm.model_validate(data)
