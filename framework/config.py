"""Central configuration, read from environment variables.

The same tests run on a laptop, inside Docker and in CI just by changing
environment variables - no code changes.
"""
import os

INSTRUMENT_HOST = os.getenv("INSTRUMENT_HOST", "")   # empty = start local sim
INSTRUMENT_PORT = int(os.getenv("INSTRUMENT_PORT", "5025"))
DASHBOARD_URL = os.getenv("DASHBOARD_URL", "")        # empty = start local app
HEADLESS = os.getenv("HEADLESS", "1") == "1"

# Test limits: the expected level and the allowed tolerance
EXPECTED_POWER_DBM = -10.0
POWER_TOLERANCE_DB = 1.0
