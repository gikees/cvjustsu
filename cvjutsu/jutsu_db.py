"""Jutsu definitions: name, seal sequence, element, effect asset."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Jutsu:
    name: str
    display: str
    element: str
    seals: list[str]
    effect_asset: str | None = None


JUTSU_LIST: list[Jutsu] = [
    Jutsu(
        name="katon_goukakyu",
        display="Katon: Goukakyu (Fireball)",
        element="Fire",
        seals=["mi", "hitsuji", "tora"],
        effect_asset="fireball.png",
    ),
    Jutsu(
        name="kage_bunshin",
        display="Kage Bunshin (Shadow Clone)",
        element="None",
        seals=["hitsuji"],
        effect_asset="shadow_clone.png",
    ),
    Jutsu(
        name="chidori",
        display="Chidori",
        element="Lightning",
        seals=["ushi", "tori", "hitsuji"],
        effect_asset="chidori.png",
    ),
]

# Index by name for quick lookup
JUTSU_BY_NAME: dict[str, Jutsu] = {j.name: j for j in JUTSU_LIST}
