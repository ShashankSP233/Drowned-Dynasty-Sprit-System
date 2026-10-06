const resourceStorageKey = "spirit-attack-builder-resources";
const embueStorageKey = "spirit-attack-builder-batches";
const riderEffects = {
  dexterity_prone: { label: "Dexterity — Prone", cost: 2 },
  strength_prone_knockback: { label: "Strength — Prone + knockback", cost: 4 },
  constitution_blind: { label: "Constitution — Blind", cost: 6 },
  strength_restrained: { label: "Strength — Restrained", cost: 8 },
  constitution_incapacitate: { label: "Constitution — Incapacitate", cost: 10 },
  difficult_terrain: { label: "Difficult terrain — 1 minute", cost: 2 },
};

const $ = (id) => document.getElementById(id);
let resources;
let batches;

function proficiencyForLevel(level) {
  return Math.floor(level / 4) + (level % 4 > 0 ? 1 : 0) + 1;
}

function readResources() {
  let saved = null;
  try {
    saved = JSON.parse(localStorage.getItem(resourceStorageKey));
  } catch {
    // Fall back to the builder's initial character values if storage is unreadable.
  }

  const level = Math.max(1, Number(saved?.level) || 5);
  const proficiency = proficiencyForLevel(level);
  const spiritMax = level * 3;
  const proficiencyMax = proficiency;
  const savedSpirit = saved?.spiritPoints == null ? spiritMax : Number(saved.spiritPoints);
  const savedProficiency = saved?.proficiencyPoints == null ? proficiencyMax : Number(saved.proficiencyPoints);
  return {
    level,
    proficiency,
    spiritPoints: Math.min(spiritMax, Math.max(0, Number.isFinite(savedSpirit) ? savedSpirit : spiritMax)),
    proficiencyPoints: Math.min(proficiencyMax, Math.max(0, Number.isFinite(savedProficiency) ? savedProficiency : proficiencyMax)),
  };
}

function saveResources() {
  try {
    localStorage.setItem(resourceStorageKey, JSON.stringify(resources));
  } catch {
    showMessage("Could not save point pools in this browser.", true);
  }
}

function readBatches() {
  try {
    const saved = JSON.parse(localStorage.getItem(embueStorageKey));
    return Array.isArray(saved) ? saved : [];
  } catch {
    return [];
  }
}

function saveBatches() {
  try {
    localStorage.setItem(embueStorageKey, JSON.stringify(batches));
  } catch {
    showMessage("Could not save Embue charges in this browser.", true);
  }
}

function heldCharges() {
  return batches.reduce((sum, batch) => sum + Math.max(0, Number(batch.remainingCharges) || 0), 0);
}

function selectedRiders() {
  return [...document.querySelectorAll(".rider:checked")].map((input) => input.value);
}

function selection() {
  const maxCharges = Math.max(0, resources.level - heldCharges());
  const charges = Math.max(1, Math.min(maxCharges, Number($("charges").value) || 1));
  const powerDice = Math.min(resources.proficiency, Math.max(0, Number($("power").value) || 0));
  const riders = selectedRiders();
  const riderCost = riders.reduce((sum, key) => sum + riderEffects[key].cost, 0);
  return {
    maxCharges,
    charges,
    powerDice,
    riders,
    riderCost,
    effectCost: powerDice + riderCost,
    totalCost: charges + powerDice + riderCost,
  };
}

function setCostRow(container, label, cost, total = false) {
  const row = document.createElement("div");
  row.className = `embue-cost-row${total ? " embue-cost-total" : ""}`;
  const name = document.createElement("span");
  name.textContent = label;
  const value = document.createElement("strong");
  value.textContent = `${cost} points`;
  row.append(name, value);
  container.append(row);
}

function renderCost() {
  const chosen = selection();
  $("power-value").textContent = `${chosen.powerDice}d6`;
  $("charges").max = Math.max(1, chosen.maxCharges);
  $("charges").disabled = chosen.maxCharges < 1;
  if (chosen.maxCharges > 0 && Number($("charges").value) > chosen.maxCharges)
    $("charges").value = chosen.maxCharges;
  const cost = $("cost-breakdown");
  cost.replaceChildren();
  $("total-cost").textContent = chosen.totalCost;
  setCostRow(cost, `Charges (${chosen.charges})`, chosen.charges);
  if (chosen.powerDice) setCostRow(cost, `Bonus Power (${chosen.powerDice}d6)`, chosen.powerDice);
  for (const rider of chosen.riders)
    setCostRow(cost, riderEffects[rider].label, riderEffects[rider].cost);
  setCostRow(cost, "Total load cost", chosen.totalCost, true);

  $("charge-limit").textContent = chosen.maxCharges
    ? `${heldCharges()} held. You can load up to ${chosen.maxCharges} more charge(s), to a maximum of ${resources.level}.`
    : `You already have the maximum ${resources.level} unused charges loaded.`;

  const affordable = chosen.totalCost <= resources.spiritPoints + resources.proficiencyPoints;
  const hasEffect = chosen.effectCost > 0;
  $("load-embue").disabled = chosen.maxCharges < 1 || !affordable || !hasEffect;
  if (!hasEffect) showMessage("Choose bonus Power or at least one rider to load.");
  else if (!affordable) showMessage("Not enough points to load these charges and effects.", true);
  else if (chosen.maxCharges < 1) showMessage("Use a hit or take a long rest to make room for charges.");
  else showMessage("");
  $("spirit-pool").textContent = `${resources.spiritPoints} / ${resources.level * 3}`;
  $("proficiency-pool").textContent = `${resources.proficiencyPoints} / ${resources.proficiency}`;
  $("held-count").textContent = `${heldCharges()} / ${resources.level} unused charges held`;
}

function renderBatches() {
  const container = $("batches");
  container.replaceChildren();
  if (!batches.length) {
    const empty = document.createElement("small");
    empty.textContent = "No Embue charges loaded.";
    container.append(empty);
    return;
  }

  for (const batch of batches) {
    const card = document.createElement("article");
    card.className = `batch-card${batch.remainingCharges === 0 ? " spent" : ""}`;
    const top = document.createElement("div");
    top.className = "batch-top";
    const title = document.createElement("div");
    title.className = "batch-title";
    title.textContent = `Embue batch ${batch.number}`;
    const remaining = document.createElement("div");
    remaining.className = "batch-remaining";
    remaining.textContent = `${batch.remainingCharges} / ${batch.totalCharges} charges`;
    top.append(title, remaining);

    const effects = document.createElement("p");
    effects.className = "batch-effects";
    const descriptions = [];
    if (batch.powerDice) descriptions.push(`${batch.powerDice}d6 bonus damage on hit`);
    for (const rider of batch.riders) descriptions.push(`${riderEffects[rider].label} on hit`);
    effects.textContent = descriptions.length ? descriptions.join(" · ") : "No effects selected";

    const spend = document.createElement("button");
    spend.type = "button";
    spend.textContent = "Mark Hit · Spend 1 Charge";
    spend.disabled = batch.remainingCharges < 1;
    spend.addEventListener("click", () => spendCharge(batch.id));
    card.append(top, effects, spend);
    container.append(card);
  }
}

function render() {
  $("power").max = resources.proficiency;
  $("power-value").textContent = `${$("power").value}d6`;
  renderCost();
  renderBatches();
}

function showMessage(message, bad = false) {
  $("message").textContent = message;
  $("message").classList.toggle("bad", bad);
}

function spendForCost(cost) {
  const fromProficiency = Math.min(resources.proficiencyPoints, cost);
  resources.proficiencyPoints -= fromProficiency;
  resources.spiritPoints -= cost - fromProficiency;
}

function loadEmbue() {
  const chosen = selection();
  if (chosen.maxCharges < 1 || chosen.effectCost < 1) return;
  if (chosen.totalCost > resources.spiritPoints + resources.proficiencyPoints) {
    showMessage("Not enough points to load these charges and effects.", true);
    return;
  }

  spendForCost(chosen.totalCost);
  batches.push({
    id: `${Date.now()}-${Math.random().toString(36).slice(2)}`,
    number: batches.length + 1,
    totalCharges: chosen.charges,
    remainingCharges: chosen.charges,
    powerDice: chosen.powerDice,
    riders: chosen.riders,
  });
  saveResources();
  saveBatches();
  render();
  showMessage(`Loaded ${chosen.charges} charge(s). Effects apply on each hit.`);
}

function spendCharge(batchId) {
  const batch = batches.find((item) => item.id === batchId);
  if (!batch || batch.remainingCharges < 1) return;
  batch.remainingCharges -= 1;
  saveBatches();
  render();
  showMessage("One charge spent on the hit.");
}

function startRound() {
  resources.proficiencyPoints = resources.proficiency;
  saveResources();
  render();
  showMessage("Proficiency points refreshed for the round.");
}

function longRest() {
  resources.spiritPoints = resources.level * 3;
  resources.proficiencyPoints = resources.proficiency;
  batches = [];
  saveResources();
  saveBatches();
  render();
  showMessage("Long rest complete. Pools restored and unused Embue charges cleared.");
}

function init() {
  resources = readResources();
  batches = readBatches();
  $("power").max = resources.proficiency;
  $("power").addEventListener("input", renderCost);
  $("charges").addEventListener("input", renderCost);
  $("embue-form").addEventListener("change", renderCost);
  $("load-embue").addEventListener("click", loadEmbue);
  $("start-round").addEventListener("click", startRound);
  $("long-rest").addEventListener("click", longRest);
  window.addEventListener("storage", (event) => {
    if (event.key === resourceStorageKey) resources = readResources();
    if (event.key === embueStorageKey) batches = readBatches();
    render();
  });
  render();
  saveResources();
}

init();
