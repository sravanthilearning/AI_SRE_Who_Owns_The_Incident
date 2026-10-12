# Presenter Runbook — Who Owns the Incident?

## Recommended environment
- Python 3.9+
- No API key or internet access required
- Works on Windows, macOS, and Linux
- All incident data are synthetic
- Remediation writes only `demo/state.json`

## Before the event (10–15 minutes)
1. Unzip the demo kit.
2. Open a terminal in the `demo` folder.
3. Run `python demo.py investigate`.
4. Run `python demo.py init`.
5. Run `python demo.py remediate` and type `APPROVE`.
6. Run `python demo.py verify`.
7. Delete `state.json` or run `python demo.py init` to reset.
8. Keep a terminal with output ready, plus the CSV/log files open in an editor.

## Live demo flow (6–8 minutes)
1. Show the alert and ask the audience what they would inspect.
2. Run `python demo.py investigate`.
3. Point to the 6x latency increase, stable CPU, slow external-risk span, retry logs, and prior retry-policy change.
4. Explain the leading hypothesis and uncertainty.
5. Ask: “Would you let the agent roll back the service?”
6. Run `python demo.py init`.
7. Run `python demo.py remediate`; first demonstrate refusing approval, then run again and type `APPROVE`.
8. Run `python demo.py verify`.
9. State clearly: this is a simulation; a real implementation must use fresh telemetry and enforce controls in code.

## Commands
```bash
python demo.py investigate
python demo.py init
python demo.py remediate
python demo.py verify
```

## Demo safety
- No external network calls.
- No Kubernetes commands.
- No production credentials.
- Do not connect a live agent to production write tools for a conference demo.
- The simulated recovery numbers are illustrative, not measured results.

## If something goes wrong
- If Python is unavailable: use the CSV/log files directly and present the expected findings from `README.md`.
- If the state file is stale: run `python demo.py init`.
- If verification says no simulated remediation exists: run `python demo.py remediate` and approve.
- If the terminal demo fails entirely: show `EXPECTED_OUTPUT.txt` and narrate the evidence chain.
