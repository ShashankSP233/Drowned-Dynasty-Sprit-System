let pyodide = null;
let calculateAttack = null;
let spiritPoints = 0;
let proficiencyPoints = 0;
let currentAttackCost = 0;
const resourceStorageKey = "spirit-attack-builder-resources";
const embueStorageKey = "spirit-attack-builder-batches";

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
  if (Number($("power").value) > level) $("power").value = level;
  $("power-value").textContent = `${$("power").value}d6`;
}

function collectAttack() {
  const riders = [...document.querySelectorAll(".rider:checked")]
    .map((x) => x.value);

  return {
    element: $("element").value,
    level: Math.max(1, Number($("level").value) || 1),
    proficiency: Number($("prof").value) || 0,
    power_dice: Number($("power").value) || 0,
    distance: Number($("distance").value) || 0,
    aoe_shape: $("aoe-enabled").checked ? $("aoe-shape").value : null,
    aoe_size: $("aoe-enabled").checked ? Number($("aoe-size").value) : null,
    embue_charges: 0,
    riders,
    element_feature: $("element-feature").checked,
    element_feature_cost_value: 1,
  };
}

function render(result) {
  $("total").textContent = result.total_cost;
  renderPools();
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

function renderPools() {
  const level = Math.max(1, Number($("level").value) || 1);
  const proficiency = Math.max(0, Number($("prof").value) || 0);
  $("spirit-pool").textContent = `${spiritPoints} / ${level * 3}`;
  $("proficiency-pool").textContent = `${proficiencyPoints} / ${proficiency}`;
}

function updatePoolMaximums() {
  const level = Math.max(1, Number($("level").value) || 1);
  const spiritMax = level * 3;
  const proficiencyMax = Math.floor(level / 4) + (level % 4 > 0 ? 1 : 0) + 1;
  $("prof").value = proficiencyMax;
  spiritPoints = Math.min(spiritPoints, spiritMax);
  proficiencyPoints = Math.min(proficiencyPoints, proficiencyMax);
  saveResources();
  renderPools();
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
    if (!saved) return false;

    const level = Math.min(20, Math.max(1, Number(saved.level) || 1));
    const proficiency = Math.floor(level / 4) + (level % 4 > 0 ? 1 : 0) + 1;
    const spiritMax = level * 3;
    const savedSpirit = saved.spiritPoints == null ? spiritMax : Number(saved.spiritPoints);
    const savedProficiency = saved.proficiencyPoints == null ? proficiency : Number(saved.proficiencyPoints);
    $("level").value = level;
    $("prof").value = proficiency;
    spiritPoints = Math.min(spiritMax, Math.max(0, Number.isFinite(savedSpirit) ? savedSpirit : spiritMax));
    proficiencyPoints = Math.min(proficiency, Math.max(0, Number.isFinite(savedProficiency) ? savedProficiency : proficiency));
    return true;
  } catch {
    try { localStorage.removeItem(resourceStorageKey); } catch { /* Ignore unavailable storage. */ }
    return false;
  }
}

function useAttack() {
  if (currentAttackCost > spiritPoints + proficiencyPoints) return;

  const fromProficiency = Math.min(proficiencyPoints, currentAttackCost);
  proficiencyPoints -= fromProficiency;
  spiritPoints -= currentAttackCost - fromProficiency;
  saveResources();
  renderPools();
  update();
}

function startRound() {
  proficiencyPoints = Math.max(0, Number($("prof").value) || 0);
  saveResources();
  renderPools();
  update();
}

function takeLongRest() {
  spiritPoints = Math.max(1, Number($("level").value) || 1) * 3;
  startRound();
  try { localStorage.removeItem(embueStorageKey); } catch { /* Ignore unavailable storage. */ }
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
  const restored = restoreResources();
  const initialLevel = Math.max(1, Number($("level").value) || 1);
  $("prof").value = Math.floor(initialLevel / 4)
    + (initialLevel % 4 > 0 ? 1 : 0) + 1;
  clampPowerToLevel();
  if (!restored) {
    spiritPoints = initialLevel * 3;
    proficiencyPoints = Number($("prof").value);
  }
  renderPools();
  saveResources();
  $("power").addEventListener("input", () => {
    $("power-value").textContent = `${$("power").value}d6`;
  });
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
  window.addEventListener("storage", (event) => {
    if (event.key === resourceStorageKey && event.newValue) {
      try {
        const saved = JSON.parse(event.newValue);
        $("level").value = saved.level;
        $("prof").value = saved.proficiency;
        spiritPoints = saved.spiritPoints;
        proficiencyPoints = saved.proficiencyPoints;
        renderPools();
        update();
      } catch {
        // Ignore incomplete data from another tab.
      }
    }
  });

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
