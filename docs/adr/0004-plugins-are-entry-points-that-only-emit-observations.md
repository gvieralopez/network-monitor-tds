# Plugins are entry points that only emit observations

Every discovery method, built-in or not, is a plugin found through the `network_monitor_tds.plugins` entry-point group, and a plugin's only output is `Observation`s handed to its `PluginContext`; it never touches the database. Built-in plugins could have been plain internal modules, but going through entry points from day one means a third-party plugin is just another installed package, and keeping plugins away from storage keeps them testable with recorded or hand-built packets.

## Consequences

- Plugin ids are a `NewType` over `str`, not an enum, because the set of plugins is open.
- The core decides what an observation means (merging facts, presence, events); plugins stay dumb.
