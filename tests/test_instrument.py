"""
Instrument-level tests: they talk to the (simulated) hardware over LAN
through the driver. This is the core of the job at Instrument Engineering.
"""
import pytest

from framework import config
from framework.instrument import InstrumentError, SignalAnalyzer


@pytest.mark.smoke
def test_identify(analyzer):
    idn = analyzer.identify()
    assert idn.startswith("SIMCORP,SA-6000"), f"Unexpected IDN: {idn}"


def test_reset_restores_default_frequency(analyzer):
    analyzer.set_frequency(2e9)
    analyzer.reset()
    assert analyzer.get_frequency() == 1e9


@pytest.mark.parametrize("freq_hz", [100e6, 1e9, 2.4e9, 3.5e9, 5.8e9])
def test_power_within_limits(analyzer, freq_hz):
    """Frequency sweep: power must be -10 dBm +/- 1 dB at every point."""
    analyzer.set_frequency(freq_hz)
    assert analyzer.get_frequency() == freq_hz

    power = analyzer.measure_power()

    expected = config.EXPECTED_POWER_DBM
    tol = config.POWER_TOLERANCE_DB
    assert abs(power - expected) <= tol, (
        f"{freq_hz / 1e6:.0f} MHz: measured {power} dBm, "
        f"expected {expected} +/- {tol} dB"
    )


def test_measurement_is_repeatable(analyzer):
    """Same setup, 5 readings: spread must be small (repeatability)."""
    analyzer.set_frequency(1e9)
    readings = [analyzer.measure_power() for _ in range(5)]
    assert max(readings) - min(readings) < 0.2, readings


@pytest.mark.parametrize("bad_freq", [1, 7e9])
def test_out_of_range_frequency_is_rejected(analyzer, bad_freq):
    with pytest.raises(InstrumentError, match="out of range"):
        analyzer.set_frequency(bad_freq)


def test_unreachable_instrument_raises_clear_error():
    sa = SignalAnalyzer("127.0.0.1", 1, timeout=0.5, retries=2)
    with pytest.raises(InstrumentError, match="Cannot connect"):
        sa.connect()
