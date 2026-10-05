# Spirit Attack Builder

    A browser-based D&D Spirit Attack builder for the Drowned Dynasty homebrew system.

## Architecture

- `web/backend/rules.py` — source-of-truth rules and costs
- `web/backend/attack.py` — attack construction and calculation
- `web/backend/player.py` — player resource model
- `web/index.html` — UI
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
- Riders use the listed costs

The elemental "Unique feature 1=each" wording and the exact Embue damage-per-charge rule are kept configurable rather than guessed.

## Next planned features

1. Better attack visualization
2. Saved/custom attacks
3. Player profiles
4. Separate reusable and spirit-form mana tracking
5. "Use Attack" button that consumes resources
6. Combat/turn reset
7. Optional online persistence for the whole party
