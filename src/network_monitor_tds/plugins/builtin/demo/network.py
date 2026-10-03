from datetime import timedelta
from ipaddress import IPv4Address

from network_monitor_tds.domain.network.models import MacAddress
from network_monitor_tds.domain.observations.models import KnownField
from network_monitor_tds.plugins.builtin.demo.models import DemoDevice, Routine

AT_START = timedelta()


def _device(
    mac: str, ip: str, routine: Routine, appears_after: timedelta, fields: dict[str, str]
) -> DemoDevice:
    return DemoDevice(MacAddress.parse(mac), IPv4Address(ip), routine, appears_after, fields)


DEVICES = (
    _device("d8:0d:17:4a:22:01", "192.168.1.1", Routine.ALWAYS, AT_START, {KnownField.VENDOR: "ZTE Corporation"}),
    _device("50:91:e3:1c:7b:40", "192.168.1.2", Routine.ALWAYS, AT_START, {KnownField.MDNS_NAME: "deco-hallway.local", KnownField.VENDOR: "TP-Link"}),
    _device("70:85:c2:9e:04:11", "192.168.1.10", Routine.ALWAYS, AT_START, {KnownField.LEASE_HOSTNAME: "homelab", KnownField.VENDOR: "ASRock Industrial"}),
    _device("dc:a6:32:58:a0:3f", "192.168.1.11", Routine.ALWAYS, AT_START, {KnownField.DHCP_HOSTNAME: "raspberrypi", KnownField.VENDOR: "Raspberry Pi Trading"}),
    _device("00:11:32:c4:7e:92", "192.168.1.12", Routine.ALWAYS, AT_START, {KnownField.MDNS_NAME: "DiskStation.local", KnownField.VENDOR: "Synology Incorporated"}),
    _device("04:7c:16:b2:5d:e8", "192.168.1.20", Routine.WORKDAY, AT_START, {KnownField.DHCP_HOSTNAME: "cachyos-ws", KnownField.VENDOR: "Micro-Star International"}),
    _device("8c:8c:aa:31:f0:62", "192.168.1.21", Routine.WORKDAY, AT_START, {KnownField.DHCP_HOSTNAME: "ThinkPad-X1", KnownField.VENDOR: "Lenovo"}),
    _device("3a:f1:5c:22:9b:07", "192.168.1.30", Routine.PHONE, AT_START, {KnownField.DHCP_HOSTNAME: "Pixel-8", KnownField.DHCP_VENDOR_CLASS: "android-dhcp-14"}),
    _device("9e:24:b8:70:1d:cc", "192.168.1.31", Routine.PHONE, AT_START, {KnownField.MDNS_NAME: "iPhone.local", KnownField.MDNS_SERVICES: "_apple-mobdev2._tcp"}),
    _device("b2:6d:0e:93:44:a5", "192.168.1.32", Routine.SPORADIC, AT_START, {KnownField.MDNS_NAME: "iPad.local"}),
    _device("a8:23:fe:10:6c:3b", "192.168.1.40", Routine.EVENING, AT_START, {KnownField.UPNP_FRIENDLY_NAME: "LG webOS TV", KnownField.VENDOR: "LG Electronics"}),
    _device("f4:f5:d8:8a:12:7e", "192.168.1.41", Routine.ALWAYS, AT_START, {KnownField.MDNS_NAME: "Chromecast.local", KnownField.MDNS_SERVICES: "_googlecast._tcp", KnownField.VENDOR: "Google"}),
    _device("1c:f2:9a:47:b3:05", "192.168.1.42", Routine.ALWAYS, AT_START, {KnownField.MDNS_NAME: "Kitchen-speaker.local", KnownField.MDNS_SERVICES: "_googlecast._tcp", KnownField.VENDOR: "Google"}),
    _device("78:c8:81:5e:2a:9d", "192.168.1.43", Routine.SPORADIC, AT_START, {KnownField.DHCP_HOSTNAME: "PS5-7A2D", KnownField.VENDOR: "Sony Interactive Entertainment"}),
    _device("64:4e:d7:0b:c9:18", "192.168.1.50", Routine.SPORADIC, AT_START, {KnownField.MDNS_NAME: "HP-LaserJet-M110w.local", KnownField.MDNS_SERVICES: "_ipp._tcp", KnownField.VENDOR: "HP Inc."}),
    _device("ec:71:db:66:0f:a2", "192.168.1.60", Routine.ALWAYS, AT_START, {KnownField.VENDOR: "Reolink Innovation"}),
    _device("3c:8a:1f:d2:47:6b", "192.168.1.70", Routine.ALWAYS, AT_START, {KnownField.DHCP_HOSTNAME: "shellyplug-s-3C8A1F", KnownField.VENDOR: "Allterco Robotics"}),
    _device("5c:62:8b:a1:e4:30", "192.168.1.71", Routine.ALWAYS, AT_START, {KnownField.DHCP_HOSTNAME: "Tapo-L530", KnownField.VENDOR: "TP-Link"}),
    _device("50:ec:50:3d:88:c7", "192.168.1.72", Routine.ALWAYS, AT_START, {KnownField.DHCP_HOSTNAME: "roborock-vacuum-s7", KnownField.VENDOR: "Roborock Technology"}),
    _device("24:0a:c4:9f:31:5e", "192.168.1.143", Routine.ALWAYS, timedelta(minutes=2), {KnownField.VENDOR: "Espressif Inc."}),
    _device("6e:b0:47:15:da:23", "192.168.1.144", Routine.PHONE, timedelta(minutes=5), {KnownField.DHCP_HOSTNAME: "android-7f3a2c9e", KnownField.DHCP_VENDOR_CLASS: "android-dhcp-14"}),
)  # fmt: skip
