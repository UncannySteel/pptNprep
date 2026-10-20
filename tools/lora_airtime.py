"""LoRa time-on-air at ABOT's radio settings, for the protocol-comparison notes.

Re-implements the Semtech AN1200.13 formula with the constants in
<CODE>/darwinV2/src/comm/phy.py:14-22 and :54-88 (SF12, 125 kHz, CR 4/5,
8-symbol preamble, explicit header, low-data-rate optimisation on).
Nothing in <CODE> is imported or run.

    python -I tools/lora_airtime.py
"""
import math

SF, BW_HZ, CR, PREAMBLE = 12, 125e3, 1, 8


def time_on_air_s(payload_bytes: int) -> float:
    t_sym = 2**SF / BW_HZ
    de = 1 if SF >= 11 else 0
    n_payload = 8 + max(
        math.ceil((8 * payload_bytes - 4 * SF + 28 + 16) / (4 * (SF - 2 * de))) * (CR + 4), 0
    )
    return (PREAMBLE + 4.25) * t_sym + n_payload * t_sym


if __name__ == "__main__":
    for n in (20, 51):
        print(f"{n:3d} B frame: {time_on_air_s(n):.2f} s on air")
    print(f"raw bit rate: {SF * BW_HZ / 2**SF * 4 / (4 + CR):.0f} bit/s")
    # One node's own airtime share for a given hello/beacon schedule.
    for label, interval_s, n in (
        ("BATMAN-adv OGM every 1 s (20 B, optimistic)", 1, 20),
        ("OLSR HELLO every 2 s (51 B, truncated)", 2, 51),
        ("Babel Hello every 4 s (51 B)", 4, 51),
        ("ABOT beacon every 30 s (20 B)", 30, 20),
    ):
        print(f"{label}: {100 * time_on_air_s(n) / interval_s:.1f}% of airtime")
