from network_monitor_tds.domain.devices.models import Category

ICONS = {
    "router": "M3 15a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2v3a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2zM7 13V7M17 13V7M7 16.5h.01M11 16.5h.01",
    "wifi": "M2 9a15 15 0 0 1 20 0M5 12.5a10 10 0 0 1 14 0M8.5 16a5 5 0 0 1 7 0M12 19.5h.01",
    "server": "M4 4h16v6H4zM4 14h16v6H4zM8 7h.01M8 17h.01",
    "disk": "M5 3h14v18H5zM9 7h6M9 11h6M9 17h.01",
    "laptop": "M5 5h14v10H5zM2 19h20",
    "desktop": "M3 4h18v12H3zM8 20h8M12 16v4",
    "phone": "M8 2h8a2 2 0 0 1 2 2v16a2 2 0 0 1-2 2H8a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2zM11 18h2",
    "tablet": "M6 2h12a2 2 0 0 1 2 2v16a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2zM11 18h2",
    "tv": "M3 7h18v12H3zM8 3l4 4 4-4",
    "speaker": "M7 2h10v20H7zM12 11a3 3 0 1 0 0 6 3 3 0 1 0 0-6M12 6h.01",
    "gamepad": "M6 11h4M8 9v4M15 12h.01M18 10h.01M17.3 5H6.7a4 4 0 0 0-4 3.6l-.7 6.3A3 3 0 0 0 7 17.6L9 15h6l2 2.6a3 3 0 0 0 5-2.7l-.7-6.3A4 4 0 0 0 17.3 5z",
    "bulb": "M9 18h6M10 22h4M12 2a6 6 0 0 0-4 10.5c.8.8 1 1.5 1 2.5h6c0-1 .2-1.7 1-2.5A6 6 0 0 0 12 2z",
    "plug": "M9 2v6M15 2v6M6 8h12v4a6 6 0 0 1-12 0zM12 18v4",
    "vacuum": "M12 3a9 9 0 1 0 0 18 9 9 0 1 0 0-18M12 9a3 3 0 1 0 0 6 3 3 0 1 0 0-6",
    "camera": "M3 7h4l2-3h6l2 3h4v13H3zM12 9a4 4 0 1 0 0 8 4 4 0 1 0 0-8",
    "printer": "M6 9V2h12v7M6 18H4v-7h16v7h-2M6 14h12v8H6z",
    "chip": "M7 7h10v10H7zM10 3v4M14 3v4M10 17v4M14 17v4M3 10h4M3 14h4M17 10h4M17 14h4",
    "question": "M12 3a9 9 0 1 0 0 18 9 9 0 1 0 0-18M9.1 9a3 3 0 0 1 5.8 1c0 2-3 3-3 3M12 17h.01",
}  # fmt: skip

CATEGORY_LABELS = {
    Category.NETWORK: "Network",
    Category.SERVER: "Server",
    Category.COMPUTER: "Computer",
    Category.PHONE: "Phone",
    Category.TABLET: "Tablet",
    Category.MEDIA: "Media",
    Category.IOT: "Smart home",
    Category.CAMERA: "Camera",
    Category.PRINTER: "Printer",
    Category.UNKNOWN: "Unknown",
}

CATEGORY_ICONS = {
    Category.NETWORK: "router",
    Category.SERVER: "server",
    Category.COMPUTER: "laptop",
    Category.PHONE: "phone",
    Category.TABLET: "tablet",
    Category.MEDIA: "tv",
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
    Category.MEDIA: "media",
    Category.IOT: "iot",
    Category.CAMERA: "camera",
    Category.PRINTER: "neutral",
    Category.UNKNOWN: "neutral",
}
