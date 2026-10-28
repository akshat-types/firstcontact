# PRESSIQ

**Is the press working—and what does winning the next duel change?**

PRESSIQ is a football tactical intelligence prototype that replays a synthetic match, connects pressing actions to recoveries and shots, and explains the evidence for casual fans and analysts.

[Deploy on Streamlit](https://share.streamlit.io/deploy?repository=akshat-types%2Ffirstcontact&branch=main&mainModule=app.py) · [Source](https://github.com/akshat-types/firstcontact)

> Hackathon MVP using fictional data and transparent scoring rules. The full dashboard works without Azure credentials. Microsoft Foundry is optional.

## Features

- **Match replay:** play, pause, step, seek and restart on a pitch event map.
- **Tactical comparison:** Lijnders-inspired counterpressing and Arteta-inspired structured pressing scores for both teams.
- **Press outcomes:** recoveries, shots after regains, bypassed presses and buildup disruption.
- **Duel impact:** compare outcomes for sequences with and without a recorded duel win.
- **Momentum:** disruption rate across each team's last five completed pressing sequences.
- **Personalization:** casual descriptions or analyst evidence, with a focus-team filter for detail tabs.
- **Insight feed:** narratives and scores unlock only after their sequence completes.
- **Export:** download completed tactical evidence.

## Get a live dashboard link

GitHub stores the source. **Streamlit Community Cloud runs the Python dashboard** and provides a shareable `streamlit.app` URL. GitHub Pages cannot run this app.

1. Open [Streamlit Community Cloud](https://share.streamlit.io/) and sign in with GitHub.
2. Select **Create app**, then **Yup, I have an app**.
3. Enter these values:

   | Setting | Value |
   | --- | --- |
   | Repository | `akshat-types/firstcontact` |
   | Branch | `main` |
   | Main file path | `app.py` |
   | Python | `3.12` in Advanced settings |
   | Secrets | Leave empty for the first demo |

4. Optionally choose an available subdomain, then click **Deploy**.
5. Verify the app, then copy its assigned URL into your repository's **About → Website** field and this README.

The deployment link above opens setup; it does not claim the app is already deployed. Streamlit assigns the actual dashboard URL. The hosted app runs independently of Colab and ngrok, using bundled CSVs. Commits to the deployed branch update the app. An inactive Community Cloud app may sleep and wake when opened.

See the [official deployment guide](https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/deploy).

## Run locally

Use Python 3.12. From the repository folder:

```bash
python -m venv .venv
# Activate: Windows .venv\Scripts\activate; macOS/Linux source .venv/bin/activate
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

The bundled demonstration match loads automatically. No API keys or ngrok token are required.

## Data and your Colab exports

| File | Contents |
| --- | --- |
| `synthetic_match.csv` | Timestamped events, locations, teams and sequence IDs |
| `pressiq_tactics.csv` | Sequence-level tactical outcomes and metrics |
| `pressiq_insights.csv` | Narratives linked to tactical evidence |

The `data/` folder contains **new reproducible demo data**, not your original Colab exports: 72 fictional pressing sequences, seed 42. Regenerate with:

```bash
python generate_demo.py --output data --seed 42 --sequences 72
```

To host your original match, replace all three CSVs in `data/` with matching Colab exports and remove `data/DEMO_DATA.md` so the app no longer identifies them as the bundled demonstration match. Commit the exports together. Match the column headers in the bundled files. Original insights without `sequence_id` are supported using minute/team/outcome matching.

For Colab, open [PRESSIQ_Colab.ipynb](PRESSIQ_Colab.ipynb) in the runtime holding your three `/content` exports. Run the install/app-writing cells, start the server and open the preview. The notebook includes an ngrok alternative. The app prioritizes existing `/content` data in Colab, then defaults to the repository's `data/` folder. Override with `PRESSIQ_DATA_DIR` or the sidebar input.

## Scoring

Python calculates every score from completed tactical records; the language model only explains evidence.

| Component | Definition |
| --- | --- |
| Counterpress rate | Regains within 5 seconds of a loss / eligible losses |
| High turnover rate | High regains (`x ≥ 66.7`) / pressing sequences |
| Disruption rate | Disrupted sequences / pressing sequences |
| Duel win rate | Recorded pressing-team wins / saved duel-contest proxy |
| Press-to-shot rate | High regains followed by a shot within 10 seconds / high regains |
| Second-ball rate | Sequences with a pressing-team second-ball win / sequences with a second-ball contest |
| Denied escape rate | Sequences without an escape label / pressing sequences |

**Lijnders-inspired** = 35% counterpress + 30% press-to-shot + 20% high turnover + 15% second ball.

**Arteta-inspired** = 35% disruption + 25% high turnover + 20% duel wins + 20% denied escape.

These are prototype archetypes, not validated ratings of coaches or teams. Zero denominators contribute zero to the composite; raw counts are visible. Fewer than five presses is a small sample.

The generator records duel winners rather than a full duel census. Impact is **association**, not proof of causation. Denied escape is a label-based proxy, not measured spatial control. A successful shot does not imply a goal. Coordinates use each sequence's pressing direction; the pitch is an event map, not player tracking.

Imported classifications are preserved. The preceding Colab engine's “High regain leading to shot” label can include a lower regain; the `high_regain` flag controls scoring. The bundled generator checks that flag when assigning the label.

## Optional later: Microsoft Foundry

Leave this unconfigured for the first deployment. Later, put these **root-level** settings in Streamlit Cloud's **App settings → Secrets**:

```toml
FOUNDRY_BASE_URL = "https://YOUR-RESOURCE.openai.azure.com/openai/v1/"
FOUNDRY_API_KEY = "YOUR-RESOURCE-KEY"
FOUNDRY_MODEL = "YOUR-DEPLOYMENT-NAME"
```

Use an OpenAI-compatible Foundry deployment supporting chat completions. The base URL ends in `/openai/v1/`; it is not a project URL. Locally, use environment variables or `.streamlit/secrets.toml`, which is excluded from Git.

Enable Foundry in the sidebar, then click **Generate Foundry commentary**. It sends the latest completed evidence only when requested. Calls use a 12-second timeout and no automatic retries. Missing credentials, inference errors and empty responses preserve rule-based commentary. AI wording is labeled and should be reviewed.

Never commit API keys, ngrok tokens, `.env` files or `secrets.toml`. The settings example contains placeholders. See [Streamlit secrets management](https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/secrets-management).

## Project structure

```text
app.py                          Dashboard
pressiq_core.py                  Validation, scores, deterministic narratives
generate_demo.py                Seeded demo generator
data/                           Three CSVs and data provenance
requirements.txt                Dependencies
.streamlit/config.toml          Theme
.streamlit/secrets.example.toml  Optional settings template
PRESSIQ_Colab.ipynb              Self-contained Colab notebook
build_notebook.py               Notebook builder
test_pressiq.py                 Data, scoring and interaction checks
.github/workflows/checks.yml    Automated checks
```

Run checks with `python -m unittest -v`. Rebuild the notebook after source changes with `python build_notebook.py`.

## Troubleshooting

- **Missing CSVs or columns:** keep matching exports together and compare the bundled headers.
- **Wrong match shown:** replace `data/` exports or choose your folder in the sidebar.
- **No insights yet:** finish a sequence or seek toward the end.
- **Deployment can't find the app:** use branch `main`, file `app.py`, and keep `requirements.txt` at the root.
- **Foundry unavailable:** rule-based mode remains usable; check your credentials later.
- **Colab reset:** `/content` is temporary; restore exports or use the hosted demo.

## Scope

Built for a time-constrained hackathon: ingest → interpret → explain → render → personalize. No real-match ingestion, player tracking, PPDA, goals model, calibrated benchmarks or persistent match database is included.
