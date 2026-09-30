"""
End-to-end UI tests with Selenium: browser -> dashboard -> instrument.
"""
import pytest

from tests.ui.pages.dashboard_page import DashboardPage


@pytest.fixture
def page(driver, dashboard_url):
    return DashboardPage(driver, dashboard_url).open()


@pytest.mark.smoke
def test_dashboard_shows_instrument_id(page):
    assert "SA-6000" in page.instrument_id()


def test_measurement_passes_at_2400_mhz(page):
    page.measure(2400)
    assert page.last_status() == "PASS"
    assert -11 <= page.last_power() <= -9


def test_invalid_input_shows_error(page):
    page.measure("abc")
    assert "valid number" in page.error_message()


def test_out_of_range_frequency_shows_instrument_error(page):
    page.measure(9000)  # 9 GHz, above the 6 GHz limit
    assert "out of range" in page.error_message()
