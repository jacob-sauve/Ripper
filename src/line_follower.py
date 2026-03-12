#!/usr/bin/env python3

"""
Line follower using a PID controller and an EV3 color sensor in "red" mode.

Strategy: follow the RIGHT edge of a black line on a white background.
The sensor targets the midpoint between white and black reflectance so
it rides the boundary — this gives a continuous, signed error signal
rather than a binary on/off response.

Orange door detection: the sensor is calibrated over the orange surface
during setup. At runtime, if the reading falls within ORANGE_TOLERANCE
of the calibrated orange value, the robot stops.

Motor DPS convention (from drive.py):
  forward  →  set_dps(-speed)   (negative)
  backward →  set_dps(+speed)   (positive)

PID correction steers by adding to one wheel and subtracting from the other:
  positive error (sees white → drifted right) → turn left
    left  = -(base - correction)   slows left wheel
    right = -(base + correction)   speeds right wheel
  negative error (sees black → drifted left) → turn right
    left  = -(base + |correction|) speeds left wheel
    right = -(base - |correction|) slows right wheel

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
HOW TO TUNE THE PID GAINS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Start with KI = 0 and KD = 0 and tune one gain at a time:

  1. Tune KP first
     - Increase KP until the robot tracks the line but oscillates (zigzags).
     - Back off KP by ~20 % to get smooth-but-responsive steering.
     - Symptom: too low  → drifts off line slowly, barely corrects.
                too high → rapid left-right oscillation (hunting).

  2. Tune KD to damp the oscillation introduced by KP
     - Increase KD gradually until the zigzag disappears.
     - KD acts on the *rate of change* of error — it brakes hard corrections
       before they overshoot, giving a crisper edge-hold.
     - Symptom: too low  → still oscillates after tuning KP.
                too high → jittery / nervous steering; sensitive to sensor noise.

  3. Add KI only if there is a persistent offset
     - A non-zero KI accumulates past error to cancel steady-state drift
       (e.g., the robot consistently hugs the wrong side of the edge).
     - Keep KI very small (0.01 – 0.1).  The anti-windup clamp (±100) limits
       runaway accumulation on long straight sections.
     - Symptom: too low  → robot wanders slightly to one side on straights.
                too high → slow oscillation that grows over time (wind-up).

  4. Adjust BASE_SPEED last
     - Higher speed needs stronger KD to stay stable.
     - Lower speed is more forgiving but slower.
     - Typical starting point: 100–200 DPS for a 1.5 cm line.
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""

import time

# ── PID gains (tune these on the actual robot) ────────────────────────────
KP = 1.2    # proportional – main steering response
KI = 0.05   # integral     – corrects slow steady-state drift
KD = 0.8    # derivative   – damps oscillation on sharp edges
# ─────────────────────────────────────────────────────────────────────────

BASE_SPEED     = 150    # DPS base forward speed
MAX_SPEED      = 350    # DPS hard cap per wheel (prevents stalling)
LOOP_HZ        = 50     # control-loop frequency (iterations/sec)
DT             = 1.0 / LOOP_HZ
ORANGE_TOLERANCE = 20   # ± this many units around orange_val triggers door stop

# Fallback calibration constants for red mode (0–255 scale).
# Always run calibrate() on the actual robot before following.
DEFAULT_WHITE  = 60
DEFAULT_BLACK  = 10
DEFAULT_ORANGE = 40     # placeholder — must be calibrated


def calibrate(sensor):
    """
    Interactive calibration for white, black, and orange surfaces.

    Returns:
        (white_val, black_val, orange_val): get_red() readings for each surface.
    """
    input("Place sensor over WHITE surface, then press Enter... ")
    white_val = sensor.get_red()
    print(f"  white  = {white_val}")

    input("Place sensor over BLACK surface, then press Enter... ")
    black_val = sensor.get_red()
    print(f"  black  = {black_val}")

    input("Place sensor over ORANGE door, then press Enter... ")
    orange_val = sensor.get_red()
    print(f"  orange = {orange_val}")

    if abs(white_val - black_val) < 10:
        print("WARNING: white/black contrast is very low — check sensor placement.")

    return white_val, black_val, orange_val


def follow_line(left, right, sensor,
                white_val=DEFAULT_WHITE, black_val=DEFAULT_BLACK,
                orange_val=DEFAULT_ORANGE, touch=None, duration=None):
    """
    PID line follower.  Stops on:
      • orange door detected (sensor reading within ORANGE_TOLERANCE of orange_val)
      • touch sensor pressed (emergency stop)
      • duration elapsed
      • Ctrl-C

    Args:
        left       : Motor object for the left wheel  (port D)
        right      : Motor object for the right wheel (port A)
        sensor     : EV3ColorSensor in 'red' mode
        white_val  : Calibrated get_red() reading over white surface
        black_val  : Calibrated get_red() reading over black surface
        orange_val : Calibrated get_red() reading over orange door
        touch      : TouchSensor for emergency stop (None = disabled)
        duration   : Seconds to run (None = run until another stop condition)

    Returns:
        str: reason for stopping — "door", "emergency_stop", "timeout", or "interrupted"
    """
    target      = (white_val + black_val) / 2.0
    stop_reason = "interrupted"

    integral   = 0.0
    prev_error = 0.0
    start      = time.time()

    print(f"Line follower started  (target={target:.1f}  white={white_val}  black={black_val}  orange={orange_val})")
    if touch is not None:
        print("Emergency stop: touch sensor on S2 active.")
    print("Press Ctrl-C to stop.\n")

    try:
        while True:
            # ── Stop conditions ───────────────────────────────────────────

            if touch is not None and touch.is_pressed():
                stop_reason = "emergency_stop"
                print("EMERGENCY STOP — touch sensor pressed!")
                break

            if duration is not None and (time.time() - start) >= duration:
                stop_reason = "timeout"
                break

            # ── Sensor read ───────────────────────────────────────────────

            reading = sensor.get_red()

            if abs(reading - orange_val) <= ORANGE_TOLERANCE:
                stop_reason = "door"
                print(f"Orange door detected (reading={reading}) — stopping.")
                break

            # ── PID ───────────────────────────────────────────────────────

            error = reading - target

            integral  += error * DT
            integral   = max(-100, min(100, integral))   # anti-windup

            derivative = (error - prev_error) / DT
            prev_error = error

            correction = KP * error + KI * integral + KD * derivative

            left_dps  = -(BASE_SPEED - correction)
            right_dps = -(BASE_SPEED + correction)

            left_dps  = max(-MAX_SPEED, min(MAX_SPEED, left_dps))
            right_dps = max(-MAX_SPEED, min(MAX_SPEED, right_dps))

            left.set_dps(left_dps)
            right.set_dps(right_dps)

            time.sleep(DT)

    except KeyboardInterrupt:
        stop_reason = "interrupted"

    finally:
        left.set_dps(0)
        right.set_dps(0)
        print(f"Line follower stopped  (reason: {stop_reason})")

    return stop_reason
