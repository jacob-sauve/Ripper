#!/usr/bin/env python3

"""
Line follower using a PID controller and an EV3 color sensor.

Strategy: follow the RIGHT edge of a black line on a white background.
The sensor targets the midpoint between white and black reflectance so
it rides the boundary — this gives a continuous, signed error signal
rather than a binary on/off response.

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
"""

import time

# ── PID gains (tune these on the actual robot) ────────────────────────────
KP = 1.2    # proportional – main steering response
KI = 0.05   # integral     – corrects slow steady-state drift
KD = 0.8    # derivative   – damps oscillation on sharp edges
# ─────────────────────────────────────────────────────────────────────────

BASE_SPEED = 150        # DPS base forward speed
MAX_SPEED  = 350        # DPS hard cap per wheel (prevents stalling)
LOOP_HZ    = 50         # control-loop frequency (iterations/sec)
DT         = 1.0 / LOOP_HZ

# Fallback calibration constants for a typical EV3 color sensor
# (override via calibrate() or pass explicit values to follow_line)
DEFAULT_WHITE = 60
DEFAULT_BLACK = 10


def calibrate(sensor):
    """
    Interactive white/black calibration.

    Returns:
        (white_val, black_val): reflected-light readings for each surface.
    """
    input("Place sensor over WHITE surface, then press Enter... ")
    white_val = sensor.get_red()
    print(f"  white = {white_val}")

    input("Place sensor over BLACK surface, then press Enter... ")
    black_val = sensor.get_red()
    print(f"  black = {black_val}")

    if abs(white_val - black_val) < 5:
        print("WARNING: white/black contrast is very low — check sensor placement.")

    return white_val, black_val


def follow_line(left, right, sensor,
                white_val=DEFAULT_WHITE, black_val=DEFAULT_BLACK,
                duration=None):
    """
    PID line follower.  Run until `duration` seconds elapse or Ctrl-C.

    Args:
        left      : Motor object for the left wheel  (port D)
        right     : Motor object for the right wheel (port A)
        sensor    : EV3ColorSensor in 'red' mode
        white_val : Calibrated reflectance reading over white surface
        black_val : Calibrated reflectance reading over black surface
        duration  : Seconds to run (None = run until KeyboardInterrupt)
    """
    target = black_val #(white_val + black_val) / 2.0

    #if (target > 20 and target < 28):
    #    return

    integral   = 0.0
    prev_error = 0.0
    start      = time.time()

    print(f"Line follower started  (target={target:.1f}  white={white_val}  black={black_val})")
    print("Press Ctrl-C to stop.\n")

    try:
        while True:
            if duration is not None and (time.time() - start) >= duration:
                break

            reading = sensor.get_red()
            error   = reading - target

            integral  += error * DT
            # Simple anti-windup: clamp integral contribution
            integral   = max(-100, min(100, integral))

            derivative = (error - prev_error) / DT
            prev_error = error

            correction = KP * error + KI * integral + KD * derivative

            left_dps  = -(BASE_SPEED - correction)
            right_dps = -(BASE_SPEED + correction)

            # Clamp each wheel independently
            left_dps  = max(-MAX_SPEED, min(MAX_SPEED, left_dps))
            right_dps = max(-MAX_SPEED, min(MAX_SPEED, right_dps))

            left.set_dps(left_dps)
            right.set_dps(right_dps)

            time.sleep(DT)

    except KeyboardInterrupt:
        pass

    except BaseException as e:
        print(e)
        
    finally:
        left.set_dps(0)
        right.set_dps(0)
        print("Line follower stopped.")
