"""Embue Tracker page (runs in the browser through PyScript).

Only page wiring lives here. The rules are in backend/embue.py and
backend/rules.py, shared with the Attack Builder.
"""

import json

from pyscript import document, window, when
from pyscript.ffi import create_proxy

from backend.embue import (
    batch_effects,
    build_macro,
    can_afford,
    held_charges,
    load_resources,
    long_rest as rest_resources,
    make_selection,
    new_batch,
    spend,
    start_round as refresh_round,
)
from backend.rules import RIDERS, max_embue_power
from character_switcher import on_character_change, selected_character_id, selected_profile

resources = {}
batches = []


def el(element_id):
    return document.getElementById(element_id)


# ---- character profile and storage -------------------------------------

def character_id():
    return selected_character_id() or "1"


def profile():
    return selected_profile()


def power_multiplier():
    try:
        return max(1, int(profile().get("power_dice_multiplier") or 1))
    except (TypeError, ValueError):
        return 1


def resource_key():
    return f"spirit-attack-builder-resources-{character_id()}"


def batch_key():
    return f"spirit-attack-builder-batches-{character_id()}"


def read_json(key, default):
    try:
        raw = window.localStorage.getItem(key)
        return json.loads(raw) if raw else default
    except Exception:
        return default


def write_json(key, value, error):
    try:
        window.localStorage.setItem(key, json.dumps(value))
    except Exception:
        show_message(error, True)


def read_resources():
    p = profile()
    return load_resources(
        read_json(resource_key(), None),
        p.get("default_level") or 4,
        p.get("default_element") or "fire",
    )


def read_batches():
    saved = read_json(batch_key(), [])
    return saved if isinstance(saved, list) else []


def save_resources():
    write_json(resource_key(), resources, "Could not save point pools in this browser.")


def save_batches():
    write_json(batch_key(), batches, "Could not save Embue charges in this browser.")


# ---- rendering ---------------------------------------------------------

def show_message(message, bad=False):
    el("message").textContent = message
    el("message").classList.toggle("bad", bad)


def selected_riders():
    return [box.value for box in document.querySelectorAll(".rider:checked")]


def current_selection():
    return make_selection(
        resources,
        batches,
        el("charges").value,
        el("power").value,
        selected_riders(),
        power_multiplier(),
    )


def add_cost_row(container, label, cost, total=False):
    row = document.createElement("div")
    row.className = "embue-cost-row" + (" embue-cost-total" if total else "")
    name = document.createElement("span")
    name.textContent = label
    value = document.createElement("strong")
    value.textContent = f"{cost} points"
    row.append(name, value)
    container.append(row)


def render_cost():
    chosen = current_selection()
    el("power-value").textContent = f"{chosen['power_dice']}d6"
    charges = el("charges")
    charges.max = str(max(1, chosen["max_charges"]))
    charges.disabled = chosen["max_charges"] < 1
    if chosen["max_charges"] > 0 and int(charges.value or 1) > chosen["max_charges"]:
        charges.value = str(chosen["max_charges"])

    container = el("cost-breakdown")
    container.replaceChildren()
    el("total-cost").textContent = str(chosen["total_cost"])
    add_cost_row(container, f"Charges ({chosen['charges']})", chosen["charges"])
    if chosen["power_dice"]:
        add_cost_row(container, f"Bonus Power ({chosen['power_dice']}d6)", chosen["power_dice"])
    for rider in chosen["riders"]:
        add_cost_row(container, RIDERS[rider][0], RIDERS[rider][1])
    add_cost_row(container, "Total load cost", chosen["total_cost"], True)

    level = resources["level"]
    held = held_charges(batches)
    el("charge-limit").textContent = (
        f"{held} held. You can load up to {chosen['max_charges']} more charge(s), to a maximum of {level}."
        if chosen["max_charges"]
        else f"You already have the maximum {level} unused charges loaded."
    )

    affordable = can_afford(resources, chosen["total_cost"])
    has_effect = chosen["effect_cost"] > 0
    el("load-embue").disabled = chosen["max_charges"] < 1 or not affordable or not has_effect
    if not has_effect:
        show_message("Choose bonus Power or at least one rider to load.")
    elif not affordable:
        show_message("Not enough points to load these charges and effects.", True)
    elif chosen["max_charges"] < 1:
        show_message("Use a hit or take a long rest to make room for charges.")
    else:
        show_message("")
    el("spirit-pool").textContent = f"{resources['spiritPoints']} / {level * 3}"
    el("proficiency-pool").textContent = f"{resources['proficiencyPoints']} / {resources['proficiency']}"
    el("held-count").textContent = f"{held} / {level} unused charges held"


def make_button(text, action, batch_id, disabled):
    button = document.createElement("button")
    button.type = "button"
    button.textContent = text
    button.disabled = disabled
    button.setAttribute("data-action", action)
    button.setAttribute("data-batch-id", batch_id)
    return button


def render_batches():
    container = el("batches")
    container.replaceChildren()
    if not batches:
        empty = document.createElement("small")
        empty.textContent = "No Embue charges loaded."
        container.append(empty)
        return

    for batch in batches:
        remaining = batch.get("remainingCharges", 0)
        card = document.createElement("article")
        card.className = "batch-card" + (" spent" if remaining == 0 else "")

        top = document.createElement("div")
        top.className = "batch-top"
        title = document.createElement("div")
        title.className = "batch-title"
        title.textContent = f"Embue batch {batch.get('number')}"
        count = document.createElement("div")
        count.className = "batch-remaining"
        count.textContent = f"{remaining} / {batch.get('totalCharges')} charges"
        top.append(title, count)

        effects = document.createElement("p")
        effects.className = "batch-effects"
        effects.textContent = batch_effects(batch)

        macro = document.createElement("textarea")
        macro.rows = 4
        macro.readOnly = True
        macro.setAttribute("aria-label", f"Roll20 macro for Embue batch {batch.get('number')}")
        macro.value = build_macro(batch, profile(), resources)

        batch_id = batch.get("id", "")
        copy_button = make_button("Copy Roll20 Macro", "copy", batch_id, remaining < 1)
        spend_button = make_button("Mark Hit · Spend 1 Charge", "spend", batch_id, remaining < 1)
        card.append(top, effects, macro, copy_button, spend_button)
        container.append(card)


def render():
    multiplier = power_multiplier()
    max_power = max_embue_power(resources["proficiency"], multiplier)
    power = el("power")
    power.max = str(max_power)
    el("power-value").textContent = f"{power.value}d6"
    note = el("power-note")
    if note:
        note.textContent = (
            f"1 point per d6. Maximum bonus Power is {multiplier}x proficiency ({max_power}d6)."
            if multiplier > 1
            else "1 point per d6. Maximum bonus Power equals proficiency."
        )
    render_cost()
    render_batches()


# ---- actions -----------------------------------------------------------

def load_embue():
    chosen = current_selection()
    if chosen["max_charges"] < 1 or chosen["effect_cost"] < 1:
        return
    if not can_afford(resources, chosen["total_cost"]):
        show_message("Not enough points to load these charges and effects.", True)
        return
    spend(resources, chosen["total_cost"])
    stamp = f"{int(window.Date.now())}-{int(window.Math.random() * 1_000_000)}"
    batches.append(new_batch(stamp, len(batches) + 1, chosen, resources, profile()))
    save_resources()
    save_batches()
    render()
    show_message(f"Loaded {chosen['charges']} charge(s). Effects apply on each hit.")


def spend_charge(batch_id):
    batch = next((b for b in batches if b.get("id") == batch_id), None)
    if not batch or batch.get("remainingCharges", 0) < 1:
        return
    batch["remainingCharges"] -= 1
    save_batches()
    render()
    show_message("One charge spent on the hit.")


async def copy_macro(batch_id):
    batch = next((b for b in batches if b.get("id") == batch_id), None)
    if not batch:
        return
    text = build_macro(batch, profile(), resources)
    try:
        await window.navigator.clipboard.writeText(text)
    except Exception:
        box = document.createElement("textarea")
        box.value = text
        document.body.append(box)
        box.select()
        document.execCommand("copy")
        box.remove()
    show_message("Roll20 macro copied.")


def start_round():
    refresh_round(resources)
    save_resources()
    render()
    show_message("Proficiency points refreshed for the round.")


def long_rest():
    global batches
    rest_resources(resources)
    batches = []
    save_resources()
    save_batches()
    render()
    show_message("Long rest complete. Pools restored and unused Embue charges cleared.")


# ---- events ------------------------------------------------------------

def on_form_change():
    render_cost()


when("input", "#power")(on_form_change)
when("input", "#charges")(on_form_change)
when("change", "#embue-form")(on_form_change)
when("click", "#load-embue")(load_embue)
when("click", "#start-round")(start_round)
when("click", "#long-rest")(long_rest)


async def on_batch_click(event):
    button = event.target.closest("button[data-action]")
    if not button:
        return
    action = button.getAttribute("data-action")
    batch_id = button.getAttribute("data-batch-id")
    if action == "spend":
        spend_charge(batch_id)
    elif action == "copy":
        await copy_macro(batch_id)


when("click", "#batches")(on_batch_click)


def reload_state(event=None):
    global resources, batches
    resources = read_resources()
    batches = read_batches()
    render()


def on_storage(event):
    global resources, batches
    if event.key == resource_key():
        resources = read_resources()
    if event.key == batch_key():
        batches = read_batches()
    render()


on_character_change(reload_state)
window.addEventListener("storage", create_proxy(on_storage))

resources = read_resources()
batches = read_batches()
render()
save_resources()
