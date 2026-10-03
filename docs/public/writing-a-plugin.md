# Writing a plugin

A plugin is a Python class installed through the `network_monitor_tds.plugins` entry-point group. Plugins only report what they see; the monitor decides what it means, stores it and shows it.

## Pick a kind

Subclass one of the base classes in `network_monitor_tds.plugins.sdk.base`:

| Base class | Method you write | When it runs |
|---|---|---|
| `ScheduledPlugin` | `async def run(self, context)` | Every `interval`, never overlapping, cancelled after `timeout`. |
| `ListenerPlugin` | `async def listen(self, context)` | Continuously; restarted with growing pauses if it crashes. |
| `EnrichmentPlugin` | `async def enrich(self, context, mac)` | Once for each known device at start, then for each new device. |

## Report what you find

The context passed to your method has two ways to report:

- `await context.sighting(mac, ip, fields)` when the device was on the network just now. Sightings create devices and mark them online.
- `await context.enrichment(mac, fields)` for information that does not prove the device is there. Enrichment for a device the monitor has never seen is ignored.

`fields` is a dictionary of strings. Use the names in `network_monitor_tds.domain.observations.models.KnownField` when they fit (`dhcp_hostname`, `mdns_name`, `vendor` …): the monitor uses them for device names and categories. Any other name is stored and shown in the device panel.

## Settings

Declare settings as a pydantic model. Scheduled plugins extend `ScheduledSettings`, others `PluginSettings`. Give every field a default; the Settings page builds its form from the model, using `title` and `description` for labels and help. Mark secrets with `Field(repr=False)`.

## Example

```python
from datetime import timedelta
from typing import ClassVar

from network_monitor_tds.domain.network.models import MacAddress
from network_monitor_tds.domain.plugins.models import PluginId
from network_monitor_tds.plugins.sdk.base import PluginContext, ScheduledPlugin
from network_monitor_tds.plugins.sdk.models import PluginInfo, ScheduledSettings


class PrinterSettings(ScheduledSettings):
    interval: timedelta = timedelta(minutes=10)
    timeout: timedelta = timedelta(seconds=30)


class PrinterPlugin(ScheduledPlugin[PrinterSettings]):
    info = PluginInfo(
        plugin_id=PluginId("office-printer"),
        name="Office printer",
        description="Reports the office printer, which never answers ARP.",
        enabled_by_default=False,
    )
    settings_model: ClassVar[type[PrinterSettings]] = PrinterSettings

    async def run(self, context: PluginContext) -> None:
        await context.sighting(MacAddress.parse("64:4e:d7:0b:c9:18"), None, {"mdns_name": "printer"})
```

Register it in your package's `pyproject.toml`, then reinstall it next to the monitor:

```toml
[project.entry-points."network_monitor_tds.plugins"]
office-printer = "my_package.printer:PrinterPlugin"
```

The plugin appears on the Settings page with the next start. Plugin ids must be unique; two plugins with the same id stop the monitor from starting.
