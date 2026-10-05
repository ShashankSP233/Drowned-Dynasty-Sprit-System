let pyodide = null;
let calculateAttack = null;

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
  const pool = level * 3;

  $("total").textContent = result.total_cost;
  $("pool").textContent = `${Math.max(0, pool - result.total_cost)} / ${pool}`;

  const over = result.total_cost > pool;
  $("warning").textContent = over
    ? "This attack costs more than the character's spirit-form mana pool."
    : "Attack is within the spirit-form mana pool.";
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

async function update() {
  if (!calculateAttack) return;

  clampPowerToLevel();

  try {
    const data = collectAttack();
    const resultJson = calculateAttack(data);
    const result = JSON.parse(resultJson);

    if (!result.valid) throw new Error("Invalid attack.");
    render(result);
  } catch (error) {
    $("warning").textContent = error.message;
    $("warning").classList.add("bad");
  }
}

async function startPython() {
  try {
    pyodide = await loadPyodide();

    await pyodide.runPythonAsync(`
import sys
sys.path.insert(0, "/app")
`);

    await pyodide.runPythonAsync(`
from attack import SpiritAttack
import json

def calculate_attack_js(data):
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
    $("warning").textContent =
      "Could not load Pyodide. Check your internet connection and run this through a web server rather than file://.";
    $("warning").classList.add("bad");
    console.error(error);
  }
}

async function loadPythonFiles() {
  // GitHub Pages serves these files normally. Pyodide's Python filesystem
  // is populated from the repository's /python directory.
  const names = ["__init__.py", "rules.py", "attack.py", "player.py"];

  for (const name of names) {
    const response = await fetch(`../python/${name}`);
    if (!response.ok) throw new Error(`Could not load ../python/${name}`);
    const text = await response.text();
    pyodide.FS.writeFile(`/app/${name}`, text);
  }
}

async function init() {
  populateAoeSizes();

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
from attack import SpiritAttack
import json

def calculate_attack_js(data):
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
