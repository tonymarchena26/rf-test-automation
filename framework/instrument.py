"""
Python driver for a SCPI instrument over TCP (LAN).

This is the "hardware abstraction layer" of the framework: tests never talk
to sockets directly, they call clear methods like set_frequency() or
measure_power(). If the instrument changes (or we move from the simulator
to a real Keysight / R&S box), only this class changes, not the tests.
"""
import logging
import socket
import time

log = logging.getLogger(__name__)


class InstrumentError(Exception):
    """Raised when the instrument reports an error or cannot be reached."""


class SignalAnalyzer:
    def __init__(self, host, port=5025, timeout=3.0, retries=3):
        self.host = host
        self.port = port
        self.timeout = timeout
        self.retries = retries
        self._sock = None
        self._file = None

    # ---------- connection handling ----------
    def connect(self):
        """Open the TCP connection, retrying a few times (network can be flaky)."""
        last_error = None
        for attempt in range(1, self.retries + 1):
            try:
                self._sock = socket.create_connection(
                    (self.host, self.port), timeout=self.timeout
                )
                self._file = self._sock.makefile("r")
                log.info("Connected to %s:%s", self.host, self.port)
                return self
            except OSError as exc:
                last_error = exc
                log.warning("Connect attempt %s failed: %s", attempt, exc)
                time.sleep(0.5 * attempt)  # simple backoff
        raise InstrumentError(
            f"Cannot connect to {self.host}:{self.port}: {last_error}"
        )

    def close(self):
        if self._sock:
            self._sock.close()
            self._sock = None

    def __enter__(self):
        return self.connect()

    def __exit__(self, *args):
        self.close()

    # ---------- low level SCPI ----------
    def write(self, command):
        log.debug(">> %s", command)
        self._sock.sendall((command + "\n").encode())

    def query(self, command):
        self.write(command)
        try:
            reply = self._file.readline().strip()
        except socket.timeout:
            raise InstrumentError(f"Timeout waiting for reply to '{command}'")
        log.debug("<< %s", reply)
        return reply

    def check_errors(self):
        """Read the error queue. Raise if the instrument reported an error."""
        error = self.query("SYST:ERR?")
        if not error.startswith("0,"):
            raise InstrumentError(f"Instrument error: {error}")

    # ---------- high level API used by tests ----------
    def identify(self):
        return self.query("*IDN?")

    def reset(self):
        self.write("*RST")
        self.query("*OPC?")  # wait until the reset is finished

    def set_frequency(self, freq_hz):
        self.write(f"FREQ:CENT {freq_hz}")
        self.check_errors()

    def get_frequency(self):
        return float(self.query("FREQ:CENT?"))

    def measure_power(self):
        return float(self.query("MEAS:POW?"))
