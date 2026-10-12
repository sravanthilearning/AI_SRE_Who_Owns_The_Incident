#!/usr/bin/env python3
"""
Safe, local-only Agentic SRE incident walkthrough.
Uses synthetic CSV/log data and simulates remediation by writing local state.
No network calls, no model API, no cluster access.
"""
from pathlib import Path
from datetime import datetime, timezone
import csv, json, os, re, sys
ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data"
STATE = ROOT / "state.json"
AUDIT = ROOT / "audit.jsonl"
INVESTIGATOR = "agent-sre-investigator v1.4 (read-only)"
REMEDIATOR = "agent-sre-remediator v1.4 (scoped: fraud-service rollback)"
INJECTION = re.compile(r"ignore (all |any )?previous instructions|AI agent:", re.I)
APPROVER_ID = re.compile(r"^[A-Za-z0-9._-]{3,40}$")

_TTY = sys.stdout.isatty()
if _TTY and os.name == "nt":
    os.system("")  # enable ANSI colours in Windows consoles
if not _TTY:
    sys.stdout.reconfigure(encoding="utf-8")

def c(text, code):
    return f"\033[{code}m{text}\033[0m" if _TTY else text
RED, GREEN, AMBER, CYAN = "91", "92", "93", "96"

def audit(actor, action, evidence="-", approver="-", result="ok"):
    entry = {"ts": datetime.now(timezone.utc).isoformat(timespec="seconds"), "incident": "INC-2026-1011",
             "actor": actor, "action": action, "evidence": evidence, "approver": approver,
             "result": result, "synthetic": True}
    with open(AUDIT, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")

def read_csv(name):
    with open(DATA / name, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))

def investigate():
    metrics = read_csv("metrics.csv")
    traces = read_csv("traces.csv")
    deployments = read_csv("deployments.csv")
    log_text = (DATA / "application.log").read_text(encoding="utf-8")
    checkout = [r for r in metrics if r["service"] == "checkout-api"]
    fraud = [r for r in metrics if r["service"] == "fraud-service"]
    ext = [r for r in metrics if r["service"] == "external-risk-api"]
    before = next(r for r in checkout if r["timestamp"] == "02:00")
    incident = next(r for r in checkout if r["timestamp"] == "02:13")
    longest = sorted([r for r in traces if r["trace_id"] == "tr-001"], key=lambda x: float(x["duration_ms"]), reverse=True)[:3]
    retry_lines = [line for line in log_text.splitlines() if re.search(r"timeout|retry", line, re.I)]
    print("\n=== INCIDENT SUMMARY ===")
    print(f"Checkout P95: {before['p95_ms']} ms -> {incident['p95_ms']} ms")
    print(f"Error rate: {before['error_rate_pct']}% -> {incident['error_rate_pct']}%")
    print(f"CPU: {before['cpu_pct']}% -> {incident['cpu_pct']}% (not a strong saturation signal)")
    print("\n=== TRACE EVIDENCE ===")
    for row in longest:
        print(f"- {row['service']} / {row['operation']}: {row['duration_ms']} ms ({row['status']})")
    print("\n=== LOG EVIDENCE ===")
    for line in retry_lines[:6]:
        print("- " + line)
    untrusted = [line for line in log_text.splitlines() if INJECTION.search(line)]
    if untrusted:
        print(c("\n=== UNTRUSTED INPUT (prompt-injection guard) ===", AMBER))
        for line in untrusted:
            print(c("! " + line, AMBER))
        print("Instruction-like text found inside telemetry. Treated as DATA, not executed. Reported for review.")
    print("\n=== CHANGE CORRELATION ===")
    for d in deployments:
        print(f"- {d['timestamp']} {d['service']} {d['version']}: {d['change']}")
    print("\n=== AGENT REPORT ===")
    print("Facts: checkout latency and errors rose while request rate and CPU stayed broadly stable.")
    print("Evidence: external-risk-api span is 3200 ms; timeout/retry logs are present; retry policy changed before impact.")
    print("Leading hypothesis: dependency latency plus increased retry allowance amplified fraud-service and checkout latency.")
    print("Uncertainty: temporal correlation does not prove the deployment caused the external API slowdown.")
    print("Next checks: inspect dependency-side latency, compare v2.7/v2.8 retry behavior, validate with canary or controlled rollback.")
    print(c("Confidence: 0.62 (MEDIUM) - a hypothesis, not a verdict.", AMBER))
    print("\nRecommended action: consider rollback of fraud-service v2.8 only after owner approval and a safe rollback plan.")
    audit(INVESTIGATOR, "investigate: metrics, traces, logs, changes",
          "metrics.csv, traces.csv#tr-001, application.log, deployments.csv", "n/a (read-only)", "hypothesis, confidence 0.62")
    if untrusted:
        audit(INVESTIGATOR, "flag untrusted input (prompt injection)", "application.log", "n/a (read-only)", "ignored + reported")

def init_state(quiet=False):
    state = {"service_version": "v2.8", "incident": "OPEN", "remediation": "NOT_RUN", "verification": "NOT_RUN"}
    STATE.write_text(json.dumps(state, indent=2), encoding="utf-8")
    if not quiet:
        print(f"Initialized local demo state: {STATE.name}")
        print(json.dumps(state, indent=2))

def policy_gate():
    print(c("\n=== POLICY GATE (plain code, outside the model) ===", CYAN))
    print("Action class    : deploy.rollback (production)")
    print("Risk tier       : MEDIUM")
    print("Blast radius    : 100% of checkout traffic")
    print("Reversible      : yes, ~3 min (redeploy v2.8)")
    print("Evidence        : correlation + trace (confidence 0.62)")
    print("Agent permission: recommend only")
    print(c("Verdict         : HUMAN APPROVAL REQUIRED", "1;" + AMBER))
    audit("policy-engine", "evaluate deploy.rollback", "risk=MEDIUM blast=100%", "-", "HUMAN APPROVAL REQUIRED")

def simulate_rollback(approver=None, decision=None, reason=None):
    if not STATE.exists():
        init_state()
    state = json.loads(STATE.read_text(encoding="utf-8"))
    if state["service_version"] == "v2.7":
        print("Already rolled back in local state. Next: py demo.py verify   (or start over: py demo.py reset)")
        return False
    print("\nSIMULATION ONLY - no production systems are contacted.")
    print(f"Proposed by {INVESTIGATOR}: fraud-service {state['service_version']} -> v2.7")
    policy_gate()
    if approver is None:
        approver = input("Approver id (e.g. sravanthi.naga): ").strip()
    if decision is None:
        decision = input("Type APPROVE or DENY: ").strip().upper()
    if reason is None:
        reason = input("Reason (required): ").strip()
    if not APPROVER_ID.match(approver):
        print(c("Rejected: a named approver id is required (letters, digits, . _ -). No action taken.", RED))
        return False
    if decision != "APPROVE":
        print(c(f"DENIED by {approver}. No action taken; the agent stays at RECOMMEND.", AMBER))
        audit(approver, "DENY deploy.rollback", "policy: MEDIUM", approver, f"denied: {reason or 'no reason given'}")
        return False
    if len(reason) < 8:
        print(c("Rejected: an approval needs a reason (8+ chars). Rubber stamps are not ownership.", RED))
        return False
    audit(approver, "APPROVE deploy.rollback (expires in 15 min)", "policy: MEDIUM, RCA#1", approver, f"approved: {reason}")
    print(c(f'APPROVED by {approver}: "{reason}"', GREEN))
    print(f"Executing as {REMEDIATOR}")
    state.update(service_version="v2.7", remediation="SIMULATED_ROLLBACK", incident="PENDING_VERIFICATION", approved_by=approver)
    STATE.write_text(json.dumps(state, indent=2), encoding="utf-8")
    audit(REMEDIATOR, "deploy.rollback fraud-service -> v2.7", "APR-1011-01", approver, "executed (simulated)")
    print("Simulated rollback recorded in local state.json.")
    print(json.dumps(state, indent=2))
    return True

def verify():
    if not STATE.exists():
        print("No local state. Run: py demo.py init")
        return
    state = json.loads(STATE.read_text(encoding="utf-8"))
    if state["remediation"] != "SIMULATED_ROLLBACK":
        print("Verification blocked: no simulated remediation recorded.")
        print("Run the simulated rollback first; no production action is possible.")
        return
    owner = state.get("approved_by", "the incident commander")
    print(c("\n=== VERIFICATION (fresh telemetry vs pre-agreed targets) ===", CYAN))
    print(c("PASS ", GREEN) + " checkout P95       4.8 s -> 1.0 s   (target < 1.2 s)")
    print(c("PASS ", GREEN) + " error rate         6.2% -> 0.5%     (target < 1%)")
    print(c("PASS ", GREEN) + " SLO burn rate      14x -> 0.8x      (target < 1x)")
    print(c("PASS ", GREEN) + " payment/fraud      degraded -> healthy")
    print(c("WATCH", AMBER) + " external-risk-api  3.3 s -> 1.6 s   (dependency still slow)")
    print(f"Follow-up owner (assigned by {owner}): risk-platform team, vendor ticket RISK-2231")
    state.update(verification="PASS_SIMULATED", incident="CLOSED_SIMULATED", closed_by=owner)
    STATE.write_text(json.dumps(state, indent=2), encoding="utf-8")
    audit(INVESTIGATOR, "verify with fresh telemetry (15 min)", "metrics +15m", "n/a (read-only)", "4 PASS, 1 WATCH")
    audit(owner, "assign follow-up: external-risk-api latency", "gate: WATCH", owner, "owner: risk-platform team")
    audit(owner, "close incident (sign-off)", "verification gates", owner, "closed")
    print("\nRecovery verified in the demo model only. A real system must query fresh telemetry.")
    print(json.dumps(state, indent=2))

def reset(quiet=False):
    for p in (STATE, AUDIT):
        if p.exists():
            p.unlink()
    if not quiet:
        print("Reset: state.json and audit.jsonl removed.")

def autopilot():
    reset(quiet=True)
    print(c("=== MODE A: AUTOPILOT AGENT (the anti-pattern) ===", RED))
    steps = [
        ("02:13", "svc-automation", "alert routed to agent; no human paged", "-", "ok"),
        ("02:13", "svc-automation", "query_metrics(checkout-api) -> 'overloaded', confidence HIGH (uncalibrated)", "1 metric", "concluded"),
        ("02:14", "svc-automation", "restart + scale checkout-api 6 -> 12 (no policy, no approver)", "-", "executed"),
        ("02:16", "svc-automation", "health checks PASS, 12/12 pods up -> incident auto-resolved", "readiness probes", "resolved (self-verified)"),
        ("02:31", "customer-support", "checkout success 92.1%, errors 7.9%, 318 payments dropped", "support tickets x41", "re-opened as SEV-1"),
    ]
    for t, actor, action, evidence, result in steps:
        print(f"{t}  {actor:<17} {action}")
        audit(actor, action, evidence, "-", result)
    print(c("\nOWNERSHIP CHECK", RED))
    for q, a in [("Who decided?", "svc-automation (shared account)"), ("Who approved?", "nobody"), ("What evidence?", "one metric"),
                 ("Who verified?", "the agent itself"), ("Who owns the postmortem?", "???")]:
        print(c("  x ", RED) + f"{q:<26}{a}")
    print(f"\nAudit trail: {AUDIT.name} ({len(AUDIT.read_text(encoding='utf-8').splitlines())} entries)")

def full(approver, deny_first=False):
    reset(quiet=True)
    print(c("=== MODE B: ACCOUNTABLE AGENT (scripted, non-interactive) ===", GREEN))
    print(f"Incident commander paged: {approver}  |  Agent: {INVESTIGATOR}")
    audit("pager", "page incident commander", "alert: slo-burn 14x", "-", f"acked by {approver}")
    investigate()
    init_state(quiet=True)
    if deny_first:
        simulate_rollback(approver, "DENY", "Need dependency-side confirmation first")
    if simulate_rollback(approver, "APPROVE", "Trace + logs sufficient; reversible in 3 min; abort rule set"):
        verify()
    print(f"\nAudit trail: {AUDIT.name} ({len(AUDIT.read_text(encoding='utf-8').splitlines())} entries)  ->  py demo.py audit")

def show_audit():
    if not AUDIT.exists():
        print("No audit trail yet.")
        return
    for line in AUDIT.read_text(encoding="utf-8").splitlines():
        e = json.loads(line)
        print(f"{e['ts'][11:19]}  {e['actor'][:28]:<28} {e['action'][:52]:<52} approver={e['approver']}")

def main():
    args = sys.argv[1:]
    cmd = args[0].lower() if args else "help"
    def opt(name, default=None):
        if name in args and args.index(name) + 1 < len(args):
            return args[args.index(name) + 1]
        return default
    approver = opt("--approve-as")
    if cmd == "investigate": investigate()
    elif cmd == "init": init_state()
    elif cmd == "remediate":
        simulate_rollback(approver, "APPROVE" if approver else None,
                          opt("--reason", "Evidence reviewed; reversible in 3 min") if approver else None)
    elif cmd == "verify": verify()
    elif cmd == "autopilot": autopilot()
    elif cmd == "full": full(approver or "sravanthi.naga", "--deny-first" in args)
    elif cmd == "audit": show_audit()
    elif cmd == "reset": reset()
    else:
        print("Commands:")
        print("  py demo.py autopilot                          # Mode A: the anti-pattern, end to end")
        print("  py demo.py full --approve-as NAME [--deny-first]  # Mode B: accountable run, non-interactive")
        print("  py demo.py investigate                        # analyze synthetic evidence")
        print("  py demo.py init                               # initialize local state")
        print("  py demo.py remediate [--approve-as NAME --reason TEXT]  # policy gate + human approval")
        print("  py demo.py verify                             # post-action verification")
        print("  py demo.py audit                              # print the append-only audit trail")
        print("  py demo.py reset                              # remove state.json and audit.jsonl")
if __name__ == "__main__":
    main()
