let pyodide = null;
let calculateAttack = null;
let spiritPoints = 0;
let proficiencyPoints = 0;
let currentAttackCost = 0;
const resourceStorageKey = "spirit-attack-builder-resources";

const $ = (id) => document.getElementById(id);

const shapes = {
  cone: [15, 30, 60, 90],
  radius: [5, 10, 15, 20, 30, 60],
  line: [30, 60, 100, 300],
};

const featureText = {
  fire: "Reroll 2 damage dice",
  water: "If the first target is hit/fails, target another creature within 10 ft for half damage",
  wood: "Next attack gains a bonus to hit",
  metal: "Next save is reduced",
  earth: "Next attack's damage is reduced",
};

function populateAoeSizes() {
  const shape = $("aoe-shape").value;
  $("aoe-size").innerHTML = shapes[shape]
    .map((size) => `<option value="${size}">${size} ft</option>`)
    .join("");
}

function clampPowerToLevel() {
  const level = Math.max(1, Number($("level").value) || 1);
  $("power").max = level;
  $("embue").max = level;
  if (Number($("power").value) > level) $("power").value = level;
  if (Number($("embue").value) > level) $("embue").value = level;
}

function collectAttack() {
  const riders = [...document.querySelectorAll(".rider:checked")]
    .map((x) => x.value);

  return {
    element: $("element").value,
    level: Math.max(1, Number($("level").value) || 1),
    proficiency: Math.max(0, Number($("prof").value) || 0),
    power_dice: Number($("power").value) || 0,
    distance: Number($("distance").value) || 0,
    aoe_shape: $("aoe-enabled").checked ? $("aoe-shape").value : null,
    aoe_size: $("aoe-enabled").checked ? Number($("aoe-size").value) : null,
    embue_charges: Number($("embue").value) || 0,
    riders,
    element_feature: $("element-feature").checked,
    element_feature_cost_value: 0,
  };
}

function render(result) {
  const level = Number($("level").value) || 1;
  const spiritMax = level * 3;
  const proficiencyMax = Math.max(0, Number($("prof").value) || 0);

  $("total").textContent = result.total_cost;
  $("spirit-pool").textContent = `${spiritPoints} / ${spiritMax}`;
  $("proficiency-pool").textContent = `${proficiencyPoints} / ${proficiencyMax}`;
  currentAttackCost = result.total_cost;
  $("use-attack").disabled = result.total_cost > spiritPoints + proficiencyPoints;

  const over = result.total_cost > spiritPoints + proficiencyPoints;
  $("warning").textContent = over
    ? "Not enough points available across both pools."
    : "Attack is affordable with your current points.";
  $("warning").classList.toggle("bad", over);

  const element = $("element").value;
  $("preview-name").textContent =
    `${element[0].toUpperCase() + element.slice(1)} Spirit Attack`;
  $("preview-damage").textContent = result.damage;

  const tags = [];
  if (Number($("distance").value)) tags.push(`${$("distance").value} ft`);
  else tags.push("Touch");

  if ($("aoe-enabled").checked)
    tags.push(`${$("aoe-shape").value} ${$("aoe-size").value} ft`);

  if (Number($("embue").value))
    tags.push(`${$("embue").value} Embue`);

  if ($("element-feature").checked)
    tags.push("Element feature");

  $("preview-tags").innerHTML =
    tags.map((x) => `<span class="tag">${x}</span>`).join("");

  $("breakdown").innerHTML = result.breakdown.length
    ? result.breakdown.map((row) =>
        `<div class="breakdown-row">
          <span>${row.category}</span>
          <span class="cost">${row.cost}</span>
        </div>`
      ).join("")
    : `<small>No optional components selected.</small>`;
}

function updatePoolMaximums() {
  const spiritMax = Math.max(1, Number($("level").value) || 1) * 3;
  const proficiencyMax = Math.max(0, Number($("prof").value) || 0);
  spiritPoints = Math.min(spiritPoints, spiritMax);
  proficiencyPoints = Math.min(proficiencyPoints, proficiencyMax);
  saveResources();
}

function saveResources() {
  try {
    localStorage.setItem(resourceStorageKey, JSON.stringify({
      level: Number($("level").value) || 1,
      proficiency: Math.max(0, Number($("prof").value) || 0),
      spiritPoints,
      proficiencyPoints,
    }));
  } catch {
    // Resource tracking still works for this page session when storage is unavailable.
  }
}

function restoreResources() {
  try {
    const saved = JSON.parse(localStorage.getItem(resourceStorageKey));
    if (saved?.level === (Number($("level").value) || 1)
      && saved?.proficiency === (Number($("prof").value) || 0)) {
      spiritPoints = Math.min(spiritPoints, Math.max(0, Number(saved.spiritPoints) || 0));
      proficiencyPoints = Math.min(proficiencyPoints, Math.max(0, Number(saved.proficiencyPoints) || 0));
    }
  } catch {
    try { localStorage.removeItem(resourceStorageKey); } catch { /* Ignore unavailable storage. */ }
  }
}

function useAttack() {
  if (currentAttackCost > spiritPoints + proficiencyPoints) return;

  const fromProficiency = Math.min(proficiencyPoints, currentAttackCost);
  proficiencyPoints -= fromProficiency;
  spiritPoints -= currentAttackCost - fromProficiency;
  saveResources();
  update();
}

function startRound() {
  proficiencyPoints = Math.max(0, Number($("prof").value) || 0);
  saveResources();
  update();
}

function takeLongRest() {
  spiritPoints = Math.max(1, Number($("level").value) || 1) * 3;
  startRound();
}

async function update() {
  if (!calculateAttack) return;

  updatePoolMaximums();
  clampPowerToLevel();

  try {
    const data = collectAttack();
    const resultJson = calculateAttack(JSON.stringify(data));
    const result = JSON.parse(resultJson);

    if (!result.valid) throw new Error("Invalid attack.");
    render(result);
  } catch (error) {
    $("warning").textContent = error.message;
    $("warning").classList.add("bad");
  }
}

async function loadPythonFiles() {
  // Keep the Python package structure so its relative imports continue to work.
  const names = ["__init__.py", "rules.py", "attack.py", "player.py"];
  pyodide.FS.mkdir("/app");
  pyodide.FS.mkdir("/app/backend");

  for (const name of names) {
    const response = await fetch(`backend/${name}`);
    if (!response.ok) throw new Error(`Could not load backend/${name}`);
    const text = await response.text();
    pyodide.FS.writeFile(`/app/backend/${name}`, text);
  }
}

async function init() {
  populateAoeSizes();
  spiritPoints = Math.max(1, Number($("level").value) || 1) * 3;
  proficiencyPoints = Math.max(0, Number($("prof").value) || 0);
  restoreResources();

  $("use-attack").addEventListener("click", useAttack);
  $("start-round").addEventListener("click", startRound);
  $("long-rest").addEventListener("click", takeLongRest);

  $("aoe-enabled").addEventListener("change", () => {
    $("aoe-controls").classList.toggle(
      "disabled",
      !$("aoe-enabled").checked
    );
    update();
  });

  $("aoe-shape").addEventListener("change", () => {
    populateAoeSizes();
    update();
  });

  $("builder").addEventListener("input", update);
  $("builder").addEventListener("change", update);

  try {
    pyodide = await loadPyodide();
    await loadPythonFiles();

    await pyodide.runPythonAsync(`
import sys
sys.path.insert(0, "/app")
`);

    await pyodide.runPythonAsync(`
from backend.attack import SpiritAttack
import json

def calculate_attack_js(data_json):
    data = json.loads(data_json)
    attack = SpiritAttack(
        element=data["element"],
        level=data["level"],
        proficiency=data["proficiency"],
        power_dice=data["power_dice"],
        distance=data["distance"],
        aoe_shape=data["aoe_shape"],
        aoe_size=data["aoe_size"],
        embue_charges=data["embue_charges"],
        riders=data["riders"],
        element_feature=data["element_feature"],
        element_feature_cost_value=data["element_feature_cost_value"],
    )
    return json.dumps(attack.calculate())
`);

    calculateAttack = pyodide.globals.get("calculate_attack_js");
    $("python-status").textContent = "Python engine ready";
    $("python-status").style.color = "#8fcf9a";
    await update();
  } catch (error) {
    $("python-status").textContent = "Python failed to load";
    $("python-status").style.color = "#e06b6b";
    $("warning").textContent = error.message;
    $("warning").classList.add("bad");
    console.error(error);
  }
}

init();
