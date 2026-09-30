# RF Test Automation Lab

A small end-to-end test automation framework for RF test equipment,
built in Python.

- **Instrument simulator**: a virtual signal analyzer that speaks SCPI over TCP (port 5025), like real Keysight / R&S instruments on a lab LAN.
- **Python driver** (`framework/instrument.py`): hardware abstraction layer with timeouts, retries and error-queue checks.
- **Instrument tests** (pytest): identification, reset, frequency sweep against power limits, repeatability, error handling.
- **Web dashboard** (Flask) + **UI tests** with Selenium and the Page Object Model.
- **Docker / docker compose**: instrument, dashboard and test runner as containers on one network.
- **CI/CD**: GitHub Actions (lint -> test -> coverage gate -> AI triage -> Docker run) and an equivalent Jenkinsfile.
- **Infrastructure as Code**: Terraform creates the lab (network + containers).
- **AI**: `tools/ai_triage.py` sends failed tests to Claude and publishes a root-cause report.

## Run locally

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
pytest                                   # 15 tests, starts simulator + dashboard itself
SIM_FAULT=drift pytest tests/test_instrument.py   # inject a hardware fault
python tools/ai_triage.py reports/junit.xml       # AI triage of the failures
```

## Run in Docker

```bash
docker compose up --build --abort-on-container-exit --exit-code-from tests
```

## Build the lab with Terraform

```bash
cd infra && terraform init && terraform apply
# dashboard at http://localhost:8080
terraform destroy
```
