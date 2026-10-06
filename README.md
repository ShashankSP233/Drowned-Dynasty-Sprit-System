# Spirit Attack Builder

    A browser-based D&D Spirit Attack builder for the Drowned Dynasty homebrew system.

## Architecture

- `web/backend/rules.py` — source-of-truth rules and costs
- `web/backend/attack.py` — attack construction and calculation
- `web/backend/player.py` — player resource model
- `web/backend/characters.py` — six starter character profiles and Spirit modifiers
- `web/index.html` — UI
- `web/embue.html` and `web/embue.js` — Embue loadout and charge tracker
- `web/style.css` — styling
- `web/app.js` — browser/Pyodide bridge
- `tests/test_rules.py` — basic Python tests

The app is designed for static hosting such as GitHub Pages. Python runs client-side through Pyodide; there is no Flask/Django server.

## Run locally

Because Pyodide is loaded by the browser, serve the `web` directory with a local HTTP server:

```bash
cd web
python -m http.server 8000
```

Then open:

`http://localhost:8000`

## GitHub Pages

The simplest deployment is to publish the `web` directory as the Pages site.

If using GitHub Actions, configure Pages to deploy the repository contents and make `web/` the published directory, or move/copy the web files to the repository root.

## Important rule notes

The initial implementation intentionally does not invent rules where the supplied document is ambiguous.

The document states:
- reusable mana = proficiency modifier, regained at the start of the turn
- spirit-form mana = 3 × level
- spirit points return on a long rest; proficiency points equal the proficiency modifier and return at the start of each round
- attacks spend proficiency points first, then spirit points
- Power = 1 point per 1d6, maximum dice equal to level
- Distance = 30/60/120/300 ft costing 1/2/3/4
- AoE cone = 2 per segment
- AoE radius = 1 per segment
- AoE line = 1 per segment
- Embue = 1 point per charge; charge maximum = level
- An Embue loadout is created as a bonus action. Its selected effects are paid once and apply to each charged hit; one charge is spent per hit.
- Embued Power is limited to proficiency. Riders are allowed; range and AoE are not.
- Unused Embue charges clear on a long rest.
- Element feature toggle = 1 point
- Riders use the listed costs
- Spirit attack bonus = Spirit modifier + proficiency; save DC = 8 + Spirit modifier + proficiency
- Starter profiles Character 1–6 currently each have a +4 Spirit modifier, default level 4, and default element Fire; each profile can be edited independently in `web/backend/characters.py`
- On first use, choose a character profile; its name stays in the top-right switcher, and each profile has separate point pools and Embue charges shared between the two pages on that browser
- The attack preview generates a copyable Roll20 macro with an attack roll, save DC, selected damage dice, and selected effects

The exact effects of each element feature follow the selected element.

## Next planned features

1. Better attack visualization
2. Saved/custom attacks
3. Player profiles
4. Separate reusable and spirit-form mana tracking
5. "Use Attack" button that consumes resources
6. Combat/turn reset
7. Optional online persistence for the whole party
