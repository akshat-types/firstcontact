"""Package a self-contained Colab notebook. Does not embed user data or secrets."""
import json
from pathlib import Path

cells = []
def markdown(text):
    cells.append(dict(cell_type='markdown', metadata={}, source=text.splitlines(True)))
def code(text):
    cells.append(dict(cell_type='code', metadata={}, execution_count=None, outputs=[], source=text.splitlines(True)))

markdown('''# PRESSIQ · Colab dashboard
Run in the **same Colab runtime** where you created the three CSVs. This notebook does not replace them.

1. Install packages and write the app using the next three cells.
2. Optionally configure Foundry before starting the server.
3. Start Streamlit and open the Colab preview. If the preview cannot maintain a WebSocket connection, use the ngrok cell instead.

The replay is synthetic. Scores are prototype heuristics, not validated coaching benchmarks. No goals are inferred from shots.
''')
code('%pip -q install "streamlit>=1.37,<2" "pandas>=2.2,<3" "plotly>=5.22,<7" "openai>=1.50,<3"\n')
for name in ['pressiq_core.py','app.py']:
    code('%%writefile /content/'+name+'\n'+Path(name).read_text(encoding='utf-8'))
markdown('''## Optional: Microsoft Foundry
Skip this cell for a fully working rule-based demo. For an OpenAI-compatible Foundry deployment, add three **Colab Secrets** and grant this notebook access:

- `FOUNDRY_BASE_URL`: resource URL ending in `/openai/v1/` (not the project URL).
- `FOUNDRY_API_KEY`: your resource key.
- `FOUNDRY_MODEL`: your deployed model/deployment name supporting chat completions.

After launching, enable Foundry in the sidebar and click **Generate Foundry commentary**. Credentials are never embedded in this notebook. A failed call falls back to deterministic text. Model wording is labeled AI wording and should be reviewed.
''')
code('''import os
from google.colab import userdata
for key in ['FOUNDRY_BASE_URL', 'FOUNDRY_API_KEY', 'FOUNDRY_MODEL']:
    try:
        os.environ[key] = userdata.get(key)
    except Exception:
        os.environ.pop(key, None)
print('Foundry configured' if all(os.getenv(k) for k in ['FOUNDRY_BASE_URL','FOUNDRY_API_KEY','FOUNDRY_MODEL']) else 'Rule-based mode ready')
''')
markdown('## Start the dashboard\nThis checks your files and starts one background server. Rerunning this cell restarts only the server created by this notebook. Keep the Colab runtime connected.')
code('''import subprocess, sys, time, urllib.request
from pathlib import Path
sys.path.insert(0, '/content')
from pressiq_core import load_data
events, tactics, insights = load_data('/content')
print(f'Ready: {len(events)} events, {len(tactics)} presses, {len(insights)} insights')
if 'pressiq_process' in globals() and pressiq_process.poll() is None:
    pressiq_process.terminate()
    pressiq_process.wait(timeout=10)
if 'pressiq_log' in globals():
    pressiq_log.close()
pressiq_log = open('/content/pressiq_streamlit.log', 'w')
pressiq_process = subprocess.Popen([
    sys.executable, '-m', 'streamlit', 'run', '/content/app.py',
    '--server.port=8501', '--server.address=0.0.0.0',
    '--server.headless=true', '--browser.gatherUsageStats=false'
], stdout=pressiq_log, stderr=subprocess.STDOUT)
for _ in range(40):
    if pressiq_process.poll() is not None:
        raise RuntimeError(Path('/content/pressiq_streamlit.log').read_text())
    try:
        with urllib.request.urlopen('http://127.0.0.1:8501/_stcore/health', timeout=1) as response:
            if response.status == 200:
                print('PRESSIQ is running on port 8501.')
                break
    except Exception:
        time.sleep(.5)
else:
    raise RuntimeError('Startup timed out. Inspect /content/pressiq_streamlit.log')
''')
code('''from google.colab import output
output.serve_kernel_port_as_window(8501)
''')
markdown('''## Alternative browser link: ngrok
Use this if the Colab preview stays blank or disconnects. Requires an ngrok account and the **NGROK_AUTHTOKEN** Colab Secret. The generated link exposes this synthetic dashboard publicly to anyone who has the URL. Stop the tunnel after the demo.
''')
code('''%pip -q install "pyngrok>=7,<10"
from pyngrok import ngrok
from google.colab import userdata
import os
os.environ['NGROK_AUTHTOKEN'] = userdata.get('NGROK_AUTHTOKEN')
if 'pressiq_tunnel' in globals():
    ngrok.disconnect(pressiq_tunnel.public_url)
pressiq_tunnel = ngrok.connect(8501, 'http')
print('Open PRESSIQ:', pressiq_tunnel.public_url)
''')
markdown('''## Two-minute demo
Click Play. Show the current sequence on the pitch, then switch between Casual fan and Analyst. Jump toward the end for both tactical scores, press outcomes, duel associations and the synchronized insight feed. Use the focus-team control to filter detail tabs; the comparison always shows both teams.

Troubleshooting: missing CSV → rerun the earlier data cells in this runtime. Missing columns/mismatched exports → regenerate tactics and insights together. A Colab reset deletes `/content`; save your CSVs first. Changing Foundry Secrets after startup requires rerunning configuration and server cells. Never paste keys into app code.

Sources: [Streamlit fragments](https://docs.streamlit.io/develop/concepts/architecture/fragments), [Foundry v1 API](https://learn.microsoft.com/en-us/azure/ai-foundry/openai/api-version-lifecycle?tabs=key), [pyngrok Colab integration](https://pyngrok.readthedocs.io/en/stable/integrations.html).
''')
code('''# Run after the demo to stop your dashboard and its optional tunnel.
if 'pressiq_tunnel' in globals():
    ngrok.disconnect(pressiq_tunnel.public_url)
if 'pressiq_process' in globals() and pressiq_process.poll() is None:
    pressiq_process.terminate()
    pressiq_process.wait(timeout=10)
if 'pressiq_log' in globals():
    pressiq_log.close()
print('PRESSIQ stopped.')
''')
notebook = dict(nbformat=4, nbformat_minor=5, metadata={'colab':{'name':'PRESSIQ_Colab.ipynb'},'kernelspec':{'display_name':'Python 3','language':'python','name':'python3'}},cells=cells)
Path('PRESSIQ_Colab.ipynb').write_text(json.dumps(notebook,indent=2),encoding='utf-8')
