"""
Shared pytest fixtures.

- If INSTRUMENT_HOST / DASHBOARD_URL are set (Docker, CI), tests use them.
- If not, the fixtures start the simulator and the dashboard locally in
  background threads, so `pytest` "just works" on a laptop.
"""
import os
import threading
from pathlib import Path

import pytest
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from werkzeug.serving import make_server

from framework import config
from framework.instrument import SignalAnalyzer
from instrument_sim.simulator import SimulatorServer

ARTIFACTS = Path("artifacts")


@pytest.fixture(scope="session")
def instrument_address():
    if config.INSTRUMENT_HOST:
        yield config.INSTRUMENT_HOST, config.INSTRUMENT_PORT
        return
    server = SimulatorServer(("127.0.0.1", 0))  # port 0 = pick a free port
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    yield server.server_address
    server.shutdown()


@pytest.fixture
def analyzer(instrument_address):
    """A connected instrument, reset before every test (clean state)."""
    host, port = instrument_address
    sa = SignalAnalyzer(host, port).connect()
    sa.reset()
    yield sa
    sa.close()


@pytest.fixture(scope="session")
def dashboard_url(instrument_address):
    if config.DASHBOARD_URL:
        yield config.DASHBOARD_URL
        return
    from dashboard.app import app
    app.config["INSTRUMENT_HOST"], app.config["INSTRUMENT_PORT"] = \
        instrument_address
    server = make_server("127.0.0.1", 0, app)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    yield f"http://127.0.0.1:{server.server_port}"
    server.shutdown()


@pytest.fixture
def driver():
    options = webdriver.ChromeOptions()
    if config.HEADLESS:
        options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1280,900")
    if os.getenv("CHROME_BIN"):  # used inside Docker
        options.binary_location = os.getenv("CHROME_BIN")
    service = Service(os.getenv("CHROMEDRIVER")) if os.getenv(
        "CHROMEDRIVER") else Service()
    drv = webdriver.Chrome(options=options, service=service)
    drv.implicitly_wait(0)  # we use explicit waits only
    yield drv
    drv.quit()


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """Take a screenshot automatically when a UI test fails."""
    outcome = yield
    report = outcome.get_result()
    if report.when == "call" and report.failed and "driver" in item.funcargs:
        ARTIFACTS.mkdir(exist_ok=True)
        path = ARTIFACTS / f"{item.name}.png"
        item.funcargs["driver"].save_screenshot(str(path))
