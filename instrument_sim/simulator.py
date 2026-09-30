"""
Simulated RF signal analyzer that speaks SCPI over TCP (port 5025).

Real instruments from Keysight, Rohde & Schwarz or Anritsu expose exactly
this kind of interface over LAN: you open a TCP socket to port 5025, send a
text command ending in a newline, and read back a text answer.

Supported commands:
    *IDN?            -> identification string
    *RST             -> reset to default state
    *OPC?            -> "1" when the operation is complete
    FREQ:CENT <Hz>   -> set centre frequency
    FREQ:CENT?       -> read centre frequency
    MEAS:POW?        -> measured power in dBm
    SYST:ERR?        -> oldest error in the queue ("0,No error" if empty)

Fault injection (to demo a failing test + AI triage):
    SIM_FAULT=drift  -> power drops 2.5 dB above 3 GHz (a "bad cable")
"""
import os
import random
import socketserver

HOST = os.getenv("SIM_HOST", "0.0.0.0")
PORT = int(os.getenv("SIM_PORT", "5025"))

MIN_FREQ_HZ = 9e3      # 9 kHz
MAX_FREQ_HZ = 6e9      # 6 GHz
SOURCE_LEVEL_DBM = -10.0  # level of the (virtual) signal generator


class InstrumentState:
    """Holds the internal state of the virtual instrument."""

    def __init__(self):
        self.reset()

    def reset(self):
        self.center_freq_hz = 1e9
        self.errors = []

    def measure_power(self):
        # Cable loss grows with frequency: ~0.1 dB per GHz
        loss_db = 0.1 * (self.center_freq_hz / 1e9)
        noise_db = random.uniform(-0.05, 0.05)
        power = SOURCE_LEVEL_DBM - loss_db + noise_db
        if os.getenv("SIM_FAULT") == "drift" and self.center_freq_hz > 3e9:
            power -= 2.5
        return round(power, 3)


def handle_command(state, line):
    """Process one SCPI command. Returns the reply or None (for writes)."""
    cmd = line.strip()
    upper = cmd.upper()

    if upper == "*IDN?":
        return "SIMCORP,SA-6000,SN0001,1.0.0"
    if upper == "*RST":
        state.reset()
        return None
    if upper == "*OPC?":
        return "1"
    if upper == "FREQ:CENT?":
        return f"{state.center_freq_hz:.0f}"
    if upper.startswith("FREQ:CENT "):
        try:
            value = float(cmd.split(" ", 1)[1])
        except ValueError:
            state.errors.append('-104,"Data type error"')
            return None
        if not MIN_FREQ_HZ <= value <= MAX_FREQ_HZ:
            state.errors.append('-222,"Data out of range"')
            return None
        state.center_freq_hz = value
        return None
    if upper == "MEAS:POW?":
        return f"{state.measure_power():.3f}"
    if upper == "SYST:ERR?":
        return state.errors.pop(0) if state.errors else '0,"No error"'

    state.errors.append('-113,"Undefined header"')
    return None


class SCPIHandler(socketserver.StreamRequestHandler):
    """One handler per TCP connection; state is shared by the server."""

    def handle(self):
        for raw in self.rfile:
            line = raw.decode().strip()
            if not line:
                continue
            reply = handle_command(self.server.state, line)
            if reply is not None:
                self.wfile.write((reply + "\n").encode())


class SimulatorServer(socketserver.ThreadingTCPServer):
    allow_reuse_address = True
    daemon_threads = True

    def __init__(self, address):
        super().__init__(address, SCPIHandler)
        self.state = InstrumentState()


if __name__ == "__main__":
    print(f"Instrument simulator listening on {HOST}:{PORT}")
    with SimulatorServer((HOST, PORT)) as server:
        server.serve_forever()
