from collections.abc import Mapping

from network_monitor_tds.domain.devices.models import (
    Category,
    ClassificationRule,
    Fallback,
    Resolved,
)
from network_monitor_tds.domain.observations.models import Fact, KnownField

NAME_RULES = (
    ClassificationRule(
        Category.WEARABLE,
        fragments=(
            "applewatch",
            "galaxywatch",
            "pixelwatch",
            "smartwatch",
            "fitbit",
            "garmin",
            "amazfit",
        ),
        words=("watch",),
    ),
    ClassificationRule(
        Category.TABLET, fragments=("ipad", "galaxytab"), words=("tablet", "tab", "kindle")
    ),
    ClassificationRule(
        Category.PHONE,
        fragments=("iphone", "android", "galaxy", "oneplus", "redmi", "xiaomi", "motorola"),
        words=("pixel", "moto"),
    ),
    ClassificationRule(
        Category.COMPUTER,
        fragments=("macbook", "laptop", "desktop", "thinkpad", "workstation"),
        words=("imac", "mac", "mbp", "pc"),
    ),
    ClassificationRule(
        Category.GAMING,
        fragments=("playstation", "xbox", "nintendo", "steamdeck", "rogally", "oculus"),
        words=("ps3", "ps4", "ps5", "quest"),
    ),
    ClassificationRule(
        Category.MEDIA,
        fragments=("chromecast", "firetv", "appletv", "webos", "bravia"),
        words=("tv", "roku", "sonos", "echo"),
    ),
    ClassificationRule(
        Category.PRINTER,
        fragments=("printer", "laserjet", "officejet", "deskjet"),
        words=("epson", "brother"),
    ),
    ClassificationRule(
        Category.CAMERA,
        fragments=("camera", "ipcam", "reolink", "hikvision", "dahua"),
        words=("cam",),
    ),
    ClassificationRule(
        Category.IOT,
        fragments=("shelly", "tasmota", "sonoff", "espressif", "roborock", "vacuum"),
        words=("esp", "esp32", "esp8266", "tapo", "tuya", "wled"),
    ),
    ClassificationRule(
        Category.SERVER,
        fragments=("synology", "diskstation", "server", "homelab", "raspberrypi", "proxmox"),
        words=("nas", "qnap", "truenas"),
    ),
    ClassificationRule(
        Category.NETWORK,
        fragments=("router", "gateway", "unifi", "openwrt", "fritz"),
        words=("deco", "mesh"),
    ),
)

SERVICE_RULES = (
    ClassificationRule(Category.PHONE, fragments=(), words=("mobdev2",)),
    ClassificationRule(
        Category.MEDIA, fragments=("spotifyconnect",), words=("googlecast", "raop", "airplay")
    ),
    ClassificationRule(
        Category.PRINTER, fragments=(), words=("ipp", "ipps", "printer", "datastream", "scanner")
    ),
    ClassificationRule(Category.CAMERA, fragments=(), words=("rtsp",)),
    ClassificationRule(Category.IOT, fragments=(), words=("hap",)),
)

VENDOR_CLASS_RULES = (
    ClassificationRule(Category.PHONE, fragments=("androiddhcp",), words=()),
    ClassificationRule(Category.COMPUTER, fragments=(), words=("msft",)),
)

VENDOR_RULES = (
    ClassificationRule(Category.WEARABLE, fragments=("fitbit", "garmin"), words=()),
    ClassificationRule(Category.GAMING, fragments=("sonyinteractive", "nintendo"), words=()),
    ClassificationRule(
        Category.IOT,
        fragments=("espressif", "shelly", "allterco", "tuya", "itead", "signify", "roborock"),
        words=(),
    ),
    ClassificationRule(Category.SERVER, fragments=("synology", "qnap", "raspberrypi"), words=()),
    ClassificationRule(
        Category.CAMERA, fragments=("reolink", "hikvision", "dahua", "axiscomm"), words=()
    ),
    ClassificationRule(Category.MEDIA, fragments=("roku", "sonos", "amazontechnologies"), words=()),
    ClassificationRule(Category.PRINTER, fragments=("seikoepson", "brotherind"), words=()),
    ClassificationRule(
        Category.NETWORK, fragments=("ubiquiti", "mikrotik", "fritz"), words=("avm",)
    ),
    ClassificationRule(
        Category.COMPUTER,
        fragments=(
            "cloudnetworktechnology",
            "honhai",
            "intelcorporate",
            "azurewave",
            "liteon",
            "gigabyte",
            "asustek",
            "microstar",
            "asrock",
        ),
        words=(),
    ),
)

RULES_BY_FIELD = (
    (KnownField.LEASE_HOSTNAME, NAME_RULES),
    (KnownField.DHCP_HOSTNAME, NAME_RULES),
    (KnownField.MDNS_NAME, NAME_RULES),
    (KnownField.UPNP_FRIENDLY_NAME, NAME_RULES),
    (KnownField.UPNP_MODEL, NAME_RULES),
    (KnownField.MDNS_SERVICES, SERVICE_RULES),
    (KnownField.DHCP_VENDOR_CLASS, VENDOR_CLASS_RULES),
    (KnownField.VENDOR, VENDOR_RULES),
)

UNCLASSIFIED = Resolved(Category.UNKNOWN, Fallback.DEFAULT)


def classify(facts: Mapping[str, Fact]) -> Resolved[Category]:
    matches = (
        Resolved(rule.category, field)
        for field, rules in RULES_BY_FIELD
        if (fact := facts.get(field)) is not None
        for rule in rules
        if rule.matches(fact.value)
    )
    return next(matches, UNCLASSIFIED)
