"""Character profiles used by the Spirit Attack Builder.

The profile data lives in characters.json so the Python rules engine
(Attack Builder) and the plain-JavaScript Embue page read the same source.
Edit each profile's name, Spirit modifier, level and element in that file.
"""

import json
from pathlib import Path

_DATA_FILE = Path(__file__).with_name("characters.json")


def _load() -> dict[str, dict[str, str | int]]:
    profiles = json.loads(_DATA_FILE.read_text(encoding="utf-8"))
    return {str(profile["id"]): profile for profile in profiles}


CHARACTERS = _load()


def list_characters() -> list[dict[str, str | int]]:
    return [CHARACTERS[key].copy() for key in sorted(CHARACTERS)]


def get_character(character_id: str) -> dict[str, str | int]:
    try:
        return CHARACTERS[str(character_id)].copy()
    except KeyError as exc:
        raise ValueError("Unknown character.") from exc
