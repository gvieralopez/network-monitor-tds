from dataclasses import dataclass

from network_monitor_tds.domain.devices.models import Category


@dataclass(frozen=True, slots=True)
class Drawing:
    name: str
    label: str
    category: Category
    footprint: int


DRAWINGS = (
    Drawing("router", "Router", Category.NETWORK, 64),
    Drawing("wifi", "Mesh point", Category.NETWORK, 34),
    Drawing("server", "Rack server", Category.SERVER, 70),
    Drawing("disk", "NAS", Category.SERVER, 42),
    Drawing("laptop", "Laptop", Category.COMPUTER, 84),
    Drawing("desktop", "Monitor", Category.COMPUTER, 34),
    Drawing("phone", "Phone, dark", Category.PHONE, 26),
    Drawing("phone-white", "Phone, white", Category.PHONE, 26),
    Drawing("tablet", "Tablet", Category.TABLET, 39),
    Drawing("watch", "Watch", Category.WEARABLE, 16),
    Drawing("tv", "TV", Category.MEDIA, 64),
    Drawing("speaker", "Smart speaker", Category.MEDIA, 26),
    Drawing("gamepad", "Controller", Category.GAMING, 59),
    Drawing("console-hybrid-duo", "Hybrid console, two-tone", Category.GAMING, 82),
    Drawing("console-hybrid-gray", "Hybrid console, grey", Category.GAMING, 82),
    Drawing("console-hybrid-dark", "Hybrid console, large dark", Category.GAMING, 82),
    Drawing("handheld-clamshell", "Clamshell handheld", Category.GAMING, 58),
    Drawing("console-tower-white", "Tower console, white", Category.GAMING, 30),
    Drawing("console-tower-black", "Tower console, black", Category.GAMING, 30),
    Drawing("chip", "Smart device", Category.IOT, 32),
    Drawing("bulb", "Smart bulb", Category.IOT, 10),
    Drawing("plug", "Smart plug", Category.IOT, 36),
    Drawing("vacuum", "Robot vacuum", Category.IOT, 72),
    Drawing("camera", "Indoor camera", Category.CAMERA, 26),
    Drawing("printer", "Printer", Category.PRINTER, 64),
    Drawing("question", "Unknown", Category.UNKNOWN, 48),
)

DRAWING_NAMES = frozenset(drawing.name for drawing in DRAWINGS)

CATEGORY_LABELS = {
    Category.NETWORK: "Network",
    Category.SERVER: "Server",
    Category.COMPUTER: "Computer",
    Category.PHONE: "Phone",
    Category.TABLET: "Tablet",
    Category.WEARABLE: "Wearable",
    Category.MEDIA: "Media",
    Category.GAMING: "Gaming",
    Category.IOT: "Smart home",
    Category.CAMERA: "Camera",
    Category.PRINTER: "Printer",
    Category.UNKNOWN: "Unknown",
}

CATEGORY_DRAWINGS = {
    Category.NETWORK: "router",
    Category.SERVER: "server",
    Category.COMPUTER: "laptop",
    Category.PHONE: "phone",
    Category.TABLET: "tablet",
    Category.WEARABLE: "watch",
    Category.MEDIA: "tv",
    Category.GAMING: "gamepad",
    Category.IOT: "chip",
    Category.CAMERA: "camera",
    Category.PRINTER: "printer",
    Category.UNKNOWN: "question",
}

CATEGORY_COLORS = {
    Category.NETWORK: "network",
    Category.SERVER: "server",
    Category.COMPUTER: "computer",
    Category.PHONE: "phone",
    Category.TABLET: "phone",
    Category.WEARABLE: "phone",
    Category.MEDIA: "media",
    Category.GAMING: "gaming",
    Category.IOT: "iot",
    Category.CAMERA: "camera",
    Category.PRINTER: "neutral",
    Category.UNKNOWN: "neutral",
}
