from collections.abc import Mapping

from network_monitor_tds.domain.observations.models import Fact, Observation


def merge_facts(current: Mapping[str, Fact], observation: Observation) -> dict[str, Fact]:
    merged = dict(current)
    for name, raw_value in observation.fields.items():
        value = raw_value.strip()
        existing = merged.get(name)
        if value and (existing is None or existing.observed_at <= observation.observed_at):
            merged[name] = Fact(
                name=name,
                value=value,
                source=observation.source,
                observed_at=observation.observed_at,
            )
    return merged
