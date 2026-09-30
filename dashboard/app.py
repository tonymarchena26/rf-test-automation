"""
Small web dashboard that lets an engineer run a power measurement on the
instrument and see PASS/FAIL against the limits. This is the UI we test
with Selenium.
"""
import os

from flask import Flask, render_template, request

from framework import config
from framework.instrument import InstrumentError, SignalAnalyzer

app = Flask(__name__)
app.config["INSTRUMENT_HOST"] = os.getenv("INSTRUMENT_HOST", "localhost")
app.config["INSTRUMENT_PORT"] = int(os.getenv("INSTRUMENT_PORT", "5025"))
results = []  # in-memory history, good enough for a demo


def instrument():
    return SignalAnalyzer(app.config["INSTRUMENT_HOST"],
                          app.config["INSTRUMENT_PORT"])


@app.route("/health")
def health():
    return {"status": "ok"}


@app.route("/", methods=["GET"])
def index():
    try:
        with instrument() as sa:
            idn = sa.identify()
    except InstrumentError as exc:
        idn = f"OFFLINE ({exc})"
    return render_template("index.html", idn=idn, results=results, error=None)


@app.route("/measure", methods=["POST"])
def measure():
    error = None
    idn = ""
    try:
        freq_mhz = float(request.form.get("freq_mhz", ""))
        with instrument() as sa:
            idn = sa.identify()
            sa.set_frequency(freq_mhz * 1e6)
            power = sa.measure_power()
        low = config.EXPECTED_POWER_DBM - config.POWER_TOLERANCE_DB
        high = config.EXPECTED_POWER_DBM + config.POWER_TOLERANCE_DB
        status = "PASS" if low <= power <= high else "FAIL"
        results.insert(0, {"freq_mhz": freq_mhz, "power": power,
                           "status": status})
    except ValueError:
        error = "Please enter a valid number"
    except InstrumentError as exc:
        error = str(exc)
    return render_template("index.html", idn=idn, results=results, error=error)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", "8080")))
