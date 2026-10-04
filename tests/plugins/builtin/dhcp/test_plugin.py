from collections.abc import AsyncIterator

import pytest
from scapy.layers.l2 import Ether
from scapy.packet import Packet

from network_monitor_tds.plugins.builtin.capture.models import PacketFilter
from network_monitor_tds.plugins.builtin.dhcp import plugin
from network_monitor_tds.plugins.builtin.dhcp.packets import DHCP_FILTER
from network_monitor_tds.plugins.builtin.dhcp.plugin import DhcpSnifferPlugin, DhcpSnifferSettings
from tests.conftest import RecordingEmit, plugin_context
from tests.plugins.builtin.dhcp.test_packets import PIXEL, REQUEST

pytestmark = pytest.mark.anyio


async def test_sniffer_reports_client_requests(monkeypatch: pytest.MonkeyPatch) -> None:
    async def fake_capture(packet_filter: PacketFilter, interface: str) -> AsyncIterator[Packet]:
        assert (packet_filter, interface) == (DHCP_FILTER, "wlan0")
        yield REQUEST
        yield Ether()

    monkeypatch.setattr(plugin, "capture", fake_capture)
    monkeypatch.setattr(plugin, "resolve_interface", lambda _configured: "wlan0")
    emit = RecordingEmit()

    await DhcpSnifferPlugin(DhcpSnifferSettings()).listen(plugin_context("dhcp-sniff", emit))

    assert [observation.mac for observation in emit.observations] == [PIXEL]
    assert emit.observations[0].fields["dhcp_hostname"] == "Pixel-8"
