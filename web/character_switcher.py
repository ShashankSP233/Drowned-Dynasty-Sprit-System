"""Character switcher shared by the Attack Builder and Embue Tracker pages.

Profiles come from backend/characters.json (through backend/characters.py), so
there is nothing to download or cache. Pages ask this module who is selected
and register a callback to be told when the player switches character.
"""

from pyscript import document, window, when
from pyscript.ffi import create_proxy

from backend.characters import list_characters

SELECTED_KEY = "spirit-attack-builder-character"

profiles = list_characters()
chosen_id = None
listeners = []


def _el(element_id):
    return document.getElementById(element_id)


def _get(key):
    try:
        return window.localStorage.getItem(key) or None
    except Exception:
        return None


def _set(key, value):
    try:
        window.localStorage.setItem(key, value)
    except Exception:
        pass


def _remove(key):
    try:
        window.localStorage.removeItem(key)
    except Exception:
        pass


# ---- what the pages use --------------------------------------------------

def selected_character_id():
    """The chosen profile id, or None until the player has chosen."""
    return chosen_id


def selected_profile():
    wanted = chosen_id or "1"
    for profile in profiles:
        if profile["id"] == wanted:
            return dict(profile)
    return dict(profiles[0])


def on_character_change(callback):
    listeners.append(callback)


def _notify():
    for callback in list(listeners):
        callback()


# ---- the switcher itself -------------------------------------------------

def _migrate_legacy_data(character_id):
    for old, new in (
        ("spirit-attack-builder-resources", f"spirit-attack-builder-resources-{character_id}"),
        ("spirit-attack-builder-batches", f"spirit-attack-builder-batches-{character_id}"),
    ):
        if not _get(new) and _get(old):
            _set(new, _get(old))
            _remove(old)


def _refresh_button():
    button = _el("active-character")
    profile = next((p for p in profiles if p["id"] == chosen_id), None)
    if profile:
        label = profile["name"]
    elif chosen_id:
        label = f"Character {chosen_id}"
    else:
        label = "Choose character"
    button.textContent = label
    button.setAttribute("aria-label", f"Current character: {label}. Click to switch.")


def _fill_choices():
    choice = _el("character-choice")
    current = choice.value or chosen_id
    options = []
    for profile in profiles:
        option = document.createElement("option")
        option.value = profile["id"]
        option.textContent = profile["name"]
        options.append(option)
    choice.replaceChildren(*options)
    if any(p["id"] == current for p in profiles):
        choice.value = current


def _open_dialog(event=None):
    _fill_choices()
    _el("cancel-character").hidden = not chosen_id
    _el("character-dialog").hidden = False
    _el("character-choice").focus()


def _update_page_links():
    for link in document.querySelectorAll(".page-nav a"):
        url = window.URL.new(link.href, window.location.href)
        if chosen_id:
            url.searchParams.set("character", chosen_id)
        else:
            url.searchParams.delete("character")
        link.href = url.href


def _confirm(event=None):
    global chosen_id
    chosen_id = str(_el("character-choice").value)
    _migrate_legacy_data(chosen_id)
    _set(SELECTED_KEY, chosen_id)
    _refresh_button()
    _update_page_links()
    _el("character-dialog").hidden = True
    next_url = window.URL.new(window.location.href)
    next_url.searchParams.set("character", chosen_id)
    window.history.replaceState(None, "", next_url.href)
    _notify()


def _cancel(event=None):
    _el("character-dialog").hidden = True


def _on_storage(event):
    global chosen_id
    if event.key == SELECTED_KEY:
        value = event.newValue
        chosen_id = str(value) if value else None
        _refresh_button()
        _update_page_links()
        _notify()


when("click", "#active-character")(_open_dialog)
when("click", "#cancel-character")(_cancel)
when("click", "#confirm-character")(_confirm)
window.addEventListener("storage", create_proxy(_on_storage))

# ---- start-up: ?character=ID in the link wins, then the saved choice ----
_page_url = window.URL.new(window.location.href)
_start = _page_url.searchParams.get("character") or _get(SELECTED_KEY)
chosen_id = str(_start) if _start else None
_fill_choices()
if chosen_id:
    _set(SELECTED_KEY, chosen_id)
    _migrate_legacy_data(chosen_id)
    _update_page_links()
    if _page_url.searchParams.has("character"):
        window.history.replaceState(None, "", _page_url.href)
_refresh_button()
if not chosen_id:
    _open_dialog()
