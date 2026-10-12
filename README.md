# Who Owns the Incident? — Accountability When AI Joins the On-Call

Live demo from the talk at **AI SRE Meetup, Hyderabad (11 Oct 2026)**.

The same 2 AM incident, handled by two AI agents:
- **A · Autopilot** — no human paged, one metric, restarts + scales production with no approval, "verifies" with its own health checks. Dashboards go green; customers keep failing.
- **B · Accountable** — a named human owns the incident, the agent investigates read-only with evidence, a policy gate requires human approval, a scoped identity runs only the approved rollback, and recovery is verified with fresh telemetry.

> **AI can take the action. Only humans can take the responsibility.**

All data is **synthetic**. Everything runs **offline** — no network, no LLM calls, no cluster access.

## Run it
| What | How |
|---|---|
| Browser demo (recommended) | Open `Demo/incident_console_v4.html` in Edge or Chrome, press **F11**. |
| Terminal backup | `cd Demo` then `python demo.py full --approve-as your.name --deny-first` |

**Keys (v4):** `→` next step · `Space` play/pause · `1×/1.5×/2×` auto-play · `S` stop · `R` reset · `1`/`2` mode A/B · `C` scorecard · `P` postmortem · `L` audit trail · `T` theme

## What's here
| Path | Contents |
|---|---|
| `Demo/incident_console_v4.html` | Latest console: four W's, step-by-step Next, reset, scorecard / postmortem / audit tabs |
| `Demo/incident_console_v3.html`, `_v2.html`, `incident_console.html` | Earlier versions of the console |
| `Demo/demo.py` | Terminal version of the same walkthrough (Python 3, standard library only) |
| `Demo/data/` | Synthetic metrics, traces, logs and deployment history |
| `Demo/PROMPTS.md` | Example prompts if you wire the evidence to a real model |
| `Notes/Demo_v4_Speaker_Notes.txt` | Step-by-step speaker notes for the v4 demo |

## The four W's — how agents fail quietly
| | Question |
|---|---|
| **W1 Wrong** | Is every claim backed by evidence? |
| **W2 Wandering** | Is it converging on the real cause? |
| **W3 Wasteful** | What is it spending while you burn? |
| **W4 Wayward** | Is it staying inside its lane? |
