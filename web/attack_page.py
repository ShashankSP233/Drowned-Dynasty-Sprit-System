"""Attack Builder page (runs in the browser through PyScript).

Only page wiring lives here. The rules are in backend/rules.py and
backend/attack.py, and the macro text is built in backend/builder.py.
"""

import json
from html import escape

from pyscript import document, window, when
from pyscript.ffi import create_proxy

from backend.builder import build_attack, build_macro, preview_tags
from backend.characters import get_character, list_characters
from backend.player import Player
from backend.rules import AOE_COSTS, ELEMENTS, proficiency_for_level
from character_switcher import on_character_change, selected_character_id, selected_profile

spirit_points = 0
proficiency_points = 0
current_attack_cost = 0


def el(element_id):
    return document.getElementById(element_id)


def number(value, default=0):
    try:
        result = float(value)
    except (TypeError, ValueError):
        return default
    return int(result) if result == result else default


def level_value():
    return max(1, number(el("level").value) or 1)


def checked_riders():
    return [box.value for box in document.querySelectorAll(".rider:checked")]


# ---- storage -------------------------------------------------------------

def resource_key():
    return f"spirit-attack-builder-resources-{selected_character_id() or '1'}"


def batch_key():
    return f"spirit-attack-builder-batches-{selected_character_id() or '1'}"


def save_resources():
    try:
        window.localStorage.setItem(resource_key(), json.dumps({
            "level": number(el("level").value) or 1,
            "default_level": selected_profile().get("default_level") or 4,
            "proficiency": max(0, number(el("prof").value)),
            "element": el("element").value,
            "spiritPoints": spirit_points,
            "proficiencyPoints": proficiency_points,
        }))
    except Exception:
        pass  # Pools still work for this page session when storage is unavailable.


def restore_resources():
    global spirit_points, proficiency_points
    try:
        raw = window.localStorage.getItem(resource_key())
        saved = json.loads(raw) if raw else None
        if not saved:
            return False
        level = min(20, max(1, number(saved.get("level")) or 1))
        proficiency = proficiency_for_level(level)
        spirit_max = level * 3
        saved_spirit = saved.get("spiritPoints")
        saved_prof = saved.get("proficiencyPoints")
        el("level").value = str(level)
        el("prof").value = str(proficiency)
        default_element = selected_profile().get("default_element") or "fire"
        el("element").value = saved.get("element") if saved.get("element") in ELEMENTS else default_element
        spirit_points = min(spirit_max, max(0, spirit_max if saved_spirit is None else number(saved_spirit, spirit_max)))
        proficiency_points = min(proficiency, max(0, proficiency if saved_prof is None else number(saved_prof, proficiency)))
        return True
    except Exception:
        try:
            window.localStorage.removeItem(resource_key())
        except Exception:
            pass
        return False


def migrate_saved_profiles():
    """Tidy old saved data from early versions (one record per character)."""
    for profile in list_characters():
        key = f"spirit-attack-builder-resources-{profile['id']}"
        try:
            raw = window.localStorage.getItem(key)
            saved = json.loads(raw) if raw else None
            if not saved:
                continue
            if saved.get("default_level") is None and number(saved.get("level")) == 5 and profile["default_level"] == 4:
                saved["level"] = profile["default_level"]
                saved["proficiency"] = proficiency_for_level(saved["level"])
                saved["spiritPoints"] = min(number(saved.get("spiritPoints")), saved["level"] * 3)
                saved["proficiencyPoints"] = min(number(saved.get("proficiencyPoints")), saved["proficiency"])
            saved["default_level"] = profile["default_level"]
            window.localStorage.setItem(key, json.dumps(saved))
        except Exception:
            continue  # Leave an unreadable record untouched.


# ---- form helpers --------------------------------------------------------

def populate_aoe_sizes():
    sizes = sorted(AOE_COSTS[el("aoe-shape").value])
    el("aoe-size").innerHTML = "".join(f'<option value="{s}">{s} ft</option>' for s in sizes)


def clamp_power_to_level():
    level = level_value()
    multiplier = max(1, number(selected_profile().get("power_dice_multiplier")) or 1)
    max_dice = level * multiplier
    power = el("power")
    power.max = str(max_dice)
    if number(power.value) > max_dice:
        power.value = str(max_dice)
    el("power-value").textContent = f"{power.value}d6"
    el("power-note").textContent = (
        f"1 point per 1d6. Maximum dice = {multiplier}x character level ({max_dice}d6 at level {level})."
        if multiplier > 1
        else "1 point per 1d6. Maximum dice = character level."
    )


def collect_attack():
    aoe_on = bool(el("aoe-enabled").checked)
    return {
        "element": el("element").value,
        "level": level_value(),
        "proficiency": number(el("prof").value),
        "power_dice": number(el("power").value),
        "distance": number(el("distance").value),
        "aoe_shape": el("aoe-shape").value if aoe_on else None,
        "aoe_size": number(el("aoe-size").value) if aoe_on else None,
        "embue_charges": 0,
        "riders": checked_riders(),
        "element_feature": bool(el("element-feature").checked),
        "element_feature_cost_value": 1,
    }


# ---- rendering -----------------------------------------------------------

def render_pools():
    el("spirit-pool").textContent = f"{spirit_points} / {level_value() * 3}"
    el("proficiency-pool").textContent = f"{proficiency_points} / {max(0, number(el('prof').value))}"


def set_warning(text, bad):
    el("warning").textContent = text
    el("warning").classList.toggle("bad", bad)


def render(result, data):
    global current_attack_cost
    total = result["total_cost"]
    current_attack_cost = total
    el("total").textContent = str(total)
    render_pools()
    over = total > spirit_points + proficiency_points
    el("use-attack").disabled = over
    set_warning(
        "Not enough points available across both pools." if over
        else "Attack is affordable with your current points.",
        over,
    )

    element = data["element"]
    el("preview-name").textContent = f"{element[:1].upper() + element[1:]} Spirit Attack"
    el("preview-damage").textContent = result["damage"]
    el("feature-text").textContent = ELEMENTS[element]["feature"]
    el("roll20-macro").value = build_macro(result, data)
    el("preview-tags").innerHTML = "".join(
        f'<span class="tag">{escape(tag)}</span>' for tag in preview_tags(result, data)
    )
    el("breakdown").innerHTML = "".join(
        f'<div class="breakdown-row"><span>{escape(row["category"])}</span>'
        f'<span class="cost">{row["cost"]}</span></div>'
        for row in result["breakdown"]
    ) or "<small>No optional components selected.</small>"


def update_pool_maximums():
    global spirit_points, proficiency_points
    level = level_value()
    proficiency_max = proficiency_for_level(level)
    el("prof").value = str(proficiency_max)
    spirit_points = min(spirit_points, level * 3)
    proficiency_points = min(proficiency_points, proficiency_max)
    save_resources()
    render_pools()


def update(event=None):
    update_pool_maximums()
    clamp_power_to_level()
    try:
        data = collect_attack()
        result = build_attack(data, get_character(selected_profile()["id"]))
        if not result.get("valid"):
            raise ValueError("Invalid attack.")
        render(result, data)
    except Exception as error:
        set_warning(str(error), True)


# ---- actions -------------------------------------------------------------

def use_attack():
    global spirit_points, proficiency_points
    if current_attack_cost > spirit_points + proficiency_points:
        return
    player = Player(
        "builder", level_value(), number(el("prof").value),
        spirit_mana=spirit_points, reusable_mana=proficiency_points,
    )
    player.use_spirit_attack(current_attack_cost)
    spirit_points, proficiency_points = player.spirit_mana, player.reusable_mana
    save_resources()
    render_pools()
    update()


def start_round():
    global proficiency_points
    proficiency_points = max(0, number(el("prof").value))
    save_resources()
    render_pools()
    update()


def take_long_rest():
    global spirit_points
    spirit_points = level_value() * 3
    start_round()
    try:
        window.localStorage.removeItem(batch_key())
    except Exception:
        pass


async def copy_macro():
    macro = el("roll20-macro").value
    try:
        await window.navigator.clipboard.writeText(macro)
    except Exception:
        el("roll20-macro").select()
        document.execCommand("copy")
    el("macro-status").textContent = "Macro copied. Paste it into Roll20 chat."


def load_selected_character():
    global spirit_points, proficiency_points
    profile = selected_profile()
    el("level").value = str(profile.get("default_level") or 4)
    el("element").value = profile.get("default_element") or "fire"
    if not restore_resources():
        level = level_value()
        el("prof").value = str(proficiency_for_level(level))
        spirit_points = level * 3
        proficiency_points = number(el("prof").value)
        save_resources()
    update()


def on_storage(event):
    global spirit_points, proficiency_points
    if event.key == resource_key() and event.newValue:
        try:
            saved = json.loads(event.newValue)
            el("level").value = str(saved["level"])
            el("prof").value = str(saved["proficiency"])
            spirit_points = saved["spiritPoints"]
            proficiency_points = saved["proficiencyPoints"]
            render_pools()
            update()
        except Exception:
            pass  # Ignore incomplete data from another tab.


def on_aoe_toggle():
    el("aoe-controls").classList.toggle("disabled", not el("aoe-enabled").checked)
    update()


def on_aoe_shape():
    populate_aoe_sizes()
    update()


def on_power_input():
    el("power-value").textContent = f"{el('power').value}d6"


# ---- events --------------------------------------------------------------

when("input", "#power")(on_power_input)
when("click", "#use-attack")(use_attack)
when("click", "#start-round")(start_round)
when("click", "#long-rest")(take_long_rest)
when("click", "#copy-macro")(copy_macro)
when("change", "#aoe-enabled")(on_aoe_toggle)
when("change", "#aoe-shape")(on_aoe_shape)
when("input", "#builder")(update)
when("change", "#builder")(update)
on_character_change(load_selected_character)
window.addEventListener("storage", create_proxy(on_storage))

# ---- start-up ------------------------------------------------------------

populate_aoe_sizes()
migrate_saved_profiles()
_profile = selected_profile()
el("level").value = str(_profile.get("default_level") or 4)
el("element").value = _profile.get("default_element") or "fire"
_restored = restore_resources()
_level = level_value()
el("prof").value = str(proficiency_for_level(_level))
if not _restored:
    spirit_points = _level * 3
    proficiency_points = number(el("prof").value)
save_resources()
update()
el("python-status").textContent = "Python engine ready"
el("python-status").style.color = "#8fcf9a"
