import hashlib
from dataclasses import dataclass
from enum import StrEnum

from network_monitor_tds.domain.network.models import MacAddress


class FillKind(StrEnum):
    DOTS = "dots"
    STRIPES = "stripes"


@dataclass(frozen=True, slots=True)
class Circle:
    cx: float
    cy: float
    r: float
    opacity: float


@dataclass(frozen=True, slots=True)
class Stroke:
    path: str
    opacity: float


@dataclass(frozen=True, slots=True)
class Fill:
    kind: FillKind
    rotation: float
    width: int


@dataclass(frozen=True, slots=True)
class Artwork:
    style: str
    pattern_id: str
    circles: tuple[Circle, ...]
    strokes: tuple[Stroke, ...]
    fill: Fill | None


def artwork(mac: MacAddress) -> Artwork:
    seed = hashlib.sha256(mac.value.encode()).digest()
    style = (
        f"--gx:{_scale(seed[1], 0, 100):.0f}%;--gy:{_scale(seed[2], 0, 60):.0f}%;"
        f"--ga:{_scale(seed[3], 110, 180):.0f}deg"
    )
    pattern_id = f"p{mac.value.replace(':', '')}"
    match seed[0] % 4:
        case 0:
            return Artwork(style, pattern_id, _rings(seed), (), None)
        case 1:
            return Artwork(style, pattern_id, (), _waves(seed), None)
        case 2:
            return Artwork(
                style, pattern_id, (), (), Fill(FillKind.DOTS, _scale(seed[6], -25, 25), 11)
            )
        case _:
            stripes = Fill(FillKind.STRIPES, _scale(seed[9], 25, 65), 5 + seed[10] % 7)
            return Artwork(style, pattern_id, (), (), stripes)


def _scale(byte: int, low: float, high: float) -> float:
    return low + byte / 255 * (high - low)


def _rings(seed: bytes) -> tuple[Circle, ...]:
    cx, cy = _scale(seed[4], 90, 160), _scale(seed[5], 0, 100)
    return tuple(Circle(cx, cy, ring * 13, 0.22 - ring * 0.018) for ring in range(1, 10))


def _waves(seed: bytes) -> tuple[Stroke, ...]:
    amplitude, offset = _scale(seed[7], 6, 16), _scale(seed[8], 0, 30)
    return tuple(
        Stroke(
            path=(
                f"M-10 {y} C {20 + offset:.1f} {y - amplitude:.1f}, {50 + offset:.1f} "
                f"{y + amplitude:.1f}, {85 + offset:.1f} {y} S {150 + offset:.1f} "
                f"{y - amplitude:.1f}, 190 {y}"
            ),
            opacity=0.08 + line * 0.02,
        )
        for line, y in enumerate(range(8, 100, 12))
    )
