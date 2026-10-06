(() => {
  const selectedKey = "spirit-attack-builder-character";
  const nameKey = "spirit-attack-builder-character-name";
  const profilesKey = "spirit-attack-builder-profiles";
  const pageUrl = new URL(window.location.href);
  const dialog = document.getElementById("character-dialog");
  const choice = document.getElementById("character-choice");
  const activeButton = document.getElementById("active-character");
  const cancelButton = document.getElementById("cancel-character");
  const confirmButton = document.getElementById("confirm-character");

  let profiles = Array.from({ length: 6 }, (_, index) => ({
    id: String(index + 1),
    name: `Character ${index + 1}`,
    spirit_modifier: 4,
    default_level: 4,
    default_element: "fire",
  }));
  try {
    const savedProfiles = JSON.parse(localStorage.getItem(profilesKey));
    if (Array.isArray(savedProfiles) && savedProfiles.length)
      profiles = savedProfiles;
  } catch {
    // The Python profiles will replace these defaults on the Attack Builder page.
  }
  let chosenId = pageUrl.searchParams.get("character") || localStorage.getItem(selectedKey);

  function migrateLegacyData(id) {
    const resourcesKey = `spirit-attack-builder-resources-${id}`;
    const batchesKey = `spirit-attack-builder-batches-${id}`;
    if (!localStorage.getItem(resourcesKey) && localStorage.getItem("spirit-attack-builder-resources")) {
      localStorage.setItem(resourcesKey, localStorage.getItem("spirit-attack-builder-resources"));
      localStorage.removeItem("spirit-attack-builder-resources");
    }
    if (!localStorage.getItem(batchesKey) && localStorage.getItem("spirit-attack-builder-batches")) {
      localStorage.setItem(batchesKey, localStorage.getItem("spirit-attack-builder-batches"));
      localStorage.removeItem("spirit-attack-builder-batches");
    }
  }

  function refreshButton() {
    const profile = profiles.find((item) => item.id === chosenId);
    const savedName = localStorage.getItem(`${nameKey}-${chosenId}`) || localStorage.getItem(nameKey);
    const profileName = profile?.name;
    activeButton.textContent = savedName || profileName || `Character ${chosenId}`;
    activeButton.setAttribute("aria-label", `Current character: ${activeButton.textContent}. Click to switch.`);
  }

  function fillChoices() {
    const current = choice.value || chosenId;
    choice.replaceChildren(...profiles.map((profile) => {
      const option = document.createElement("option");
      option.value = profile.id;
      option.textContent = localStorage.getItem(`${nameKey}-${profile.id}`) || profile.name;
      return option;
    }));
    if (profiles.some((profile) => profile.id === current)) choice.value = current;
  }

  function openDialog() {
    fillChoices();
    cancelButton.hidden = !chosenId;
    dialog.hidden = false;
    choice.focus();
  }

  function setProfiles(nextProfiles) {
    profiles = nextProfiles;
    localStorage.setItem(profilesKey, JSON.stringify(profiles));
    for (const profile of profiles)
      localStorage.setItem(`${nameKey}-${profile.id}`, profile.name);
    fillChoices();
    if (chosenId) {
      const selected = profiles.find((profile) => profile.id === chosenId);
      if (selected) localStorage.setItem(nameKey, selected.name);
    }
    refreshButton();
  }

  function selectedCharacterId() {
    return chosenId;
  }

  function selectedCharacterProfile() {
    return profiles.find((profile) => profile.id === (chosenId || "1")) || profiles[0];
  }

  function updatePageLinks() {
    document.querySelectorAll(".page-nav a").forEach((link) => {
      const url = new URL(link.href, window.location.href);
      if (chosenId) url.searchParams.set("character", chosenId);
      else url.searchParams.delete("character");
      link.href = url.href;
    });
  }

  activeButton.addEventListener("click", openDialog);
  cancelButton.addEventListener("click", () => { dialog.hidden = true; });
  confirmButton.addEventListener("click", () => {
    chosenId = choice.value;
    migrateLegacyData(chosenId);
    const profile = profiles.find((item) => item.id === chosenId);
    localStorage.setItem(selectedKey, chosenId);
    if (profile) {
      const profileName = localStorage.getItem(`${nameKey}-${profile.id}`) || profile.name;
      localStorage.setItem(nameKey, profileName);
      localStorage.setItem(`${nameKey}-${profile.id}`, profileName);
    }
    refreshButton();
    updatePageLinks();
    dialog.hidden = true;
    const nextUrl = new URL(window.location.href);
    nextUrl.searchParams.set("character", chosenId);
    history.replaceState(null, "", nextUrl);
    window.dispatchEvent(new CustomEvent("characterchange", { detail: { id: chosenId } }));
  });
  window.addEventListener("storage", (event) => {
    if (event.key === selectedKey) {
      chosenId = event.newValue;
      refreshButton();
      updatePageLinks();
      window.dispatchEvent(new CustomEvent("characterchange", { detail: { id: chosenId } }));
    }
  });

  fillChoices();
  if (chosenId) {
    localStorage.setItem(selectedKey, chosenId);
    migrateLegacyData(chosenId);
    updatePageLinks();
    if (pageUrl.searchParams.has("character")) history.replaceState(null, "", pageUrl);
  }
  refreshButton();
  if (!chosenId) openDialog();
  window.setCharacterProfiles = setProfiles;
  window.selectedCharacterId = selectedCharacterId;
  window.selectedCharacterProfile = selectedCharacterProfile;
})();
