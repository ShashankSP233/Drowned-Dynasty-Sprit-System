"""Character profiles used by the Spirit Attack Builder."""

# Edit each profile's name and Spirit modifier independently.
CHARACTERS = {
    "1": {"id": "1", "name": "Sion Luminous", "spirit_modifier": 4, "default_level": 4, "default_element": "fire"},
    "2": {"id": "2", "name": "Xaioli", "spirit_modifier": 4, "default_level": 4, "default_element": "wood"},
    "3": {"id": "3", "name": "Garris", "spirit_modifier": 4, "default_level": 4, "default_element": "metal"},
    "4": {"id": "4", "name": "Craig", "spirit_modifier": 3, "default_level": 4, "default_element": "earth"},
    "5": {"id": "5", "name": "Ying Yue", "spirit_modifier": 4, "default_level": 4, "default_element": "water"},
    "6": {"id": "6", "name": "Light (DM)", "spirit_modifier": 4, "default_level": 4, "default_element": "fire"},
}


def list_characters() -> list[dict[str, str | int]]:
    return [CHARACTERS[key].copy() for key in sorted(CHARACTERS)]


def get_character(character_id: str) -> dict[str, str | int]:
    try:
        return CHARACTERS[str(character_id)].copy()
    except KeyError as exc:
        raise ValueError("Unknown character.") from exc
