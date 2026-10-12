# Demo Scenario: Checkout Latency Incident

**Important:** All data is synthetic and the remediation is simulated. Do not connect this demo to production credentials.

## Incident
At 02:13, checkout P95 latency rises from ~800 ms to ~4.8 s and error rate reaches ~6.2%. Request rate and CPU remain broadly stable.

## Data files
- `data/metrics.csv` — latency, error rate, request rate, CPU and memory samples.
- `data/application.log` — time-correlated timeout and retry evidence.
- `data/traces.csv` — baseline and incident distributed traces.
- `data/deployments.csv` — a recent change to the fraud-service retry policy.

## Expected investigation conclusion
Leading hypothesis: the external risk API latency increase, combined with the changed retry policy in `fraud-service` v2.8, amplifies downstream latency and causes checkout timeouts.

This is a **hypothesis supported by the synthetic evidence**, not proof of causation. A production investigation would validate with change comparison, dependency telemetry, and a controlled rollback/canary or equivalent test.

## Live-demo sequence (6–8 minutes)
1. Show the alert: checkout P95 4.8 s; error rate 6.2%; request rate stable; CPU normal.
2. Ask the audience what they would inspect first.
3. Open `traces.csv`: the critical path spends 3.2 s in `external-risk-api`; retries add further delay.
4. Search `application.log` for `timeout` and `retry`.
5. Open `deployments.csv`: retry policy changed at 01:56, before symptom onset.
6. Ask the agent to produce facts, hypotheses, counter-evidence, and next validation steps.
7. Present a proposed rollback of `fraud-service` v2.8. Do **not** execute a real production action.
8. Run the included simulated remediation command; it changes only a local JSON state file.
9. Run verification and show recovery. Explain that a real environment must verify using fresh telemetry and predefined stop conditions.

## Suggested narration
“The agent did not magically know the root cause. It correlated three kinds of evidence, checked the timeline, and produced a hypothesis. The SRE still needs to validate whether the deployment caused the issue and whether rollback is safe.”
