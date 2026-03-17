"""
ECSE211 – Smart Hospital Assistant Robot
Room Subsystem Module
=====================
Handles everything that happens once the robot has detected the orange doorway
and needs to enter the patient room:
  1. Drive through the orange doorway into the room
  2. Sweep left-to-right to locate a bed indicator (green or red sticker)
  3. Decide whether to drop a foam cube (green = yes, red = no)
  4. Handle double-occupancy rooms (scan for a second bed after the first)
  5. Locate the orange doorway again and exit back to the corridor

Hardware assumed:
  - BrickPi3 board running on a Raspberry Pi
  - Two drive motors (left: PORT_B, right: PORT_C) — adjust to your wiring
  - One delivery/drop motor (PORT_A) — adjust to your mechanism
  - Color sensor on PORT_1 (facing the floor)
  - Speaker driven via subprocess calls to 'aplay' (WAV files)

Author : Marny Brooker
Date   : March 2026
Version: 1.0
"""

import time
import subprocess         
import brickpi3            

# ---------------------------------------------------------------------------
# Hardware port assignments — change these to match your physical wiring
# ---------------------------------------------------------------------------
LEFT_MOTOR_PORT  = brickpi3.BrickPi3.PORT_B
RIGHT_MOTOR_PORT = brickpi3.BrickPi3.PORT_C
DROP_MOTOR_PORT  = brickpi3.BrickPi3.PORT_A   # Motor that releases a foam cube
COLOR_SENSOR_PORT = brickpi3.BrickPi3.PORT_1

# ---------------------------------------------------------------------------
# Speed constants (degrees per second — tune during testing)
# ---------------------------------------------------------------------------
DRIVE_SPEED       = 150   # Forward/backward driving speed
SWEEP_SPEED       = 80    # Slow rotation speed used while scanning for beds
EXIT_SEARCH_SPEED = 70    # Rotation speed while hunting for the orange exit

# ---------------------------------------------------------------------------
# Timing constants (seconds — tune during testing)
# ---------------------------------------------------------------------------
ROOM_ENTRY_DURATION   = 1.2   # Time to drive forward after crossing the orange line
                               # (enough to clear the doorway so orange isn't re-detected)
EXIT_DRIVE_DURATION   = 1.5   # Time to drive forward after relocating the orange exit
SWEEP_TIMEOUT         = 12.0  # Max seconds to sweep before giving up on finding a bed
EXIT_SEARCH_TIMEOUT   = 15.0  # Max seconds to search for the orange exit tile
SWEEP_LEFT_DURATION   = 2.5   # How long to turn left during one sweep arc
SWEEP_RIGHT_DURATION  = 2.5   # How long to turn right during one sweep arc (return arc)

# ---------------------------------------------------------------------------
# Color classification thresholds (RGB — calibrate with your actual sensor!)
# ---------------------------------------------------------------------------
# The BrickPi3 color sensor in COLOR_COLOR_COMPONENTS mode returns (R, G, B, ambient).
# These are *example* ranges; you MUST run calibration tests in your actual arena lighting.
#
# Tip: print raw sensor values while placing the sensor over each tile and record the ranges.

def classify_color(rgb):
    """
    Classify a raw RGB reading from the color sensor into a colour label.

    Parameters
    ----------
    rgb : tuple
        (R, G, B, ambient) from bp.get_sensor() in COLOR_COLOR_COMPONENTS mode.

    Returns
    -------
    str : one of "ORANGE", "GREEN", "RED", "YELLOW", "BLUE", "UNKNOWN"
    """
    r, g, b, _ = rgb   # discard the ambient channel

    # --- ORANGE detection (doorway tile) ---
    # Orange has high red, moderate green, very low blue.
    if r > 150 and 60 < g < 140 and b < 60:
        return "ORANGE"

    # --- GREEN detection (bed requires medication) ---
    # Green has low red, high green, low-to-moderate blue.
    if r < 100 and g > 100 and b < 100:
        return "GREEN"

    # --- RED detection (bed does NOT require medication) ---
    # Red has high red, low green, low blue.
    if r > 120 and g < 80 and b < 80:
        return "RED"

    # --- YELLOW detection (patient room floor tile) ---
    # Yellow has high red AND high green, low blue.
    if r > 120 and g > 120 and b < 80:
        return "YELLOW"

    # --- BLUE detection (pharmacy tile) ---
    if b > 120 and r < 80 and g < 80:
        return "BLUE"

    return "UNKNOWN"


# ---------------------------------------------------------------------------
# Low-level motor helpers
# ---------------------------------------------------------------------------

def drive_forward(bp, duration):
    """
    Drive both motors forward at DRIVE_SPEED for the given duration (seconds),
    then stop.
    """
    bp.set_motor_dps(LEFT_MOTOR_PORT,  DRIVE_SPEED)
    bp.set_motor_dps(RIGHT_MOTOR_PORT, DRIVE_SPEED)
    time.sleep(duration)
    stop_robot(bp)


def drive_backward(bp, duration):
    """Drive both motors in reverse for the given duration, then stop."""
    bp.set_motor_dps(LEFT_MOTOR_PORT,  -DRIVE_SPEED)
    bp.set_motor_dps(RIGHT_MOTOR_PORT, -DRIVE_SPEED)
    time.sleep(duration)
    stop_robot(bp)


def stop_robot(bp):
    """Immediately stop all drive motors."""
    bp.set_motor_dps(LEFT_MOTOR_PORT,  0)
    bp.set_motor_dps(RIGHT_MOTOR_PORT, 0)


def rotate_left(bp):
    """
    Start a continuous left rotation (in-place) at SWEEP_SPEED.
    Call stop_robot() to halt.
    """
    bp.set_motor_dps(LEFT_MOTOR_PORT,  -SWEEP_SPEED)
    bp.set_motor_dps(RIGHT_MOTOR_PORT,  SWEEP_SPEED)


def rotate_right(bp):
    """
    Start a continuous right rotation (in-place) at SWEEP_SPEED.
    Call stop_robot() to halt.
    """
    bp.set_motor_dps(LEFT_MOTOR_PORT,   SWEEP_SPEED)
    bp.set_motor_dps(RIGHT_MOTOR_PORT, -SWEEP_SPEED)


def rotate_for_exit(bp):
    """
    Slow rotation used while searching for the orange exit tile.
    Turning right by default; the exit_room function reverses direction
    if needed.
    """
    bp.set_motor_dps(LEFT_MOTOR_PORT,   EXIT_SEARCH_SPEED)
    bp.set_motor_dps(RIGHT_MOTOR_PORT, -EXIT_SEARCH_SPEED)


# ---------------------------------------------------------------------------
# Delivery helper
# ---------------------------------------------------------------------------




# def drop_cube(bp):




# ---------------------------------------------------------------------------
# Color sensor helper
# ---------------------------------------------------------------------------

def read_color(bp):
    """
    Read the color sensor and return a classified color string.

    Returns
    -------
    str : "ORANGE", "GREEN", "RED", "YELLOW", "BLUE", or "UNKNOWN"
    """
    try:
        raw = bp.get_sensor(COLOR_SENSOR_PORT)  # Returns (R, G, B, ambient)
        label = classify_color(raw)
        return label
    except brickpi3.SensorError as e:
        print(f"[SENSOR] Color sensor error: {e}")
        return "UNKNOWN"


# ---------------------------------------------------------------------------
# Core bed-scanning sweep
# ---------------------------------------------------------------------------

def sweep_for_beds(bp, color_sensor_port, cubes_remaining):
    """
    Perform a left-to-right sweep inside the room to locate bed indicator stickers.
    Stops when it reads GREEN or RED, handles the delivery decision, then continues
    the sweep to find a second bed (for double-occupancy rooms).

    The sweep pattern:
        1. Rotate left for SWEEP_LEFT_DURATION seconds (or until a bed is found)
        2. Rotate right back through centre and continue for SWEEP_RIGHT_DURATION
           seconds (or until a second bed is found / timeout)
        3. Return to approximately centre-facing orientation

    Parameters
    ----------
    bp              : BrickPi3 instance
    color_sensor_port : not used directly here (uses the module-level constant),
                       kept as parameter for clarity / future refactoring
    cubes_remaining : int — how many foam cubes the robot is still carrying

    Returns
    -------
    cubes_remaining : int — updated cube count after any deliveries in this room
    """

    beds_scanned  = 0   # How many beds we found during this sweep
    sweep_timeout = time.time() + SWEEP_TIMEOUT

    print("[SWEEP] Beginning left arc...")

    # ---- Phase 1: Sweep LEFT ------------------------------------------------
    rotate_left(bp)
    phase1_end = time.time() + SWEEP_LEFT_DURATION

    while time.time() < phase1_end and time.time() < sweep_timeout:
        color = read_color(bp)

        if color in ("GREEN", "RED"):
            stop_robot(bp)
            print(f"[SWEEP] Bed found during left arc — color: {color}")
            cubes_remaining = handle_bed(bp, color, cubes_remaining)
            beds_scanned += 1

            # Brief pause after delivery before continuing the sweep
            time.sleep(0.4)

            # Resume leftward sweep to look for a second bed
            rotate_left(bp)

        time.sleep(0.05)   # Short polling interval (50 ms)

    stop_robot(bp)

    # If we already found 2 beds (max for double-occupancy), no need for phase 2
    if beds_scanned >= 2:
        print("[SWEEP] Both beds found during left arc. Sweep complete.")
        return cubes_remaining

    print("[SWEEP] Beginning right arc (returning through centre)...")

    # ---- Phase 2: Sweep RIGHT (return arc) ----------------------------------
    rotate_right(bp)
    # The right arc is longer: it returns through centre AND continues right
    phase2_end = time.time() + (SWEEP_LEFT_DURATION + SWEEP_RIGHT_DURATION)

    while time.time() < phase2_end and time.time() < sweep_timeout:
        color = read_color(bp)

        if color in ("GREEN", "RED"):
            stop_robot(bp)
            print(f"[SWEEP] Bed found during right arc — color: {color}")
            cubes_remaining = handle_bed(bp, color, cubes_remaining)
            beds_scanned += 1

            if beds_scanned >= 2:
                break   # Found both beds, stop sweeping

            # Resume rightward sweep
            rotate_right(bp)

        time.sleep(0.05)

    stop_robot(bp)

    # ---- Phase 3: Return to approximately centre-facing ---------------------
    # After the full right arc, rotate left for half the right-arc duration
    # to end up roughly where we started (facing the room interior).
    print("[SWEEP] Re-centering robot orientation...")
    rotate_left(bp)
    time.sleep(SWEEP_RIGHT_DURATION / 2)
    stop_robot(bp)

    if beds_scanned == 0:
        print("[SWEEP] WARNING: No bed stickers detected within timeout.")

    print(f"[SWEEP] Sweep complete. Beds scanned: {beds_scanned}. "
          f"Cubes remaining: {cubes_remaining}.")

    return cubes_remaining


def handle_bed(bp, color, cubes_remaining):
    """
    Decide what to do at a detected bed based on its color indicator.

    Parameters
    ----------
    bp              : BrickPi3 instance
    color           : str — "GREEN" or "RED"
    cubes_remaining : int — cubes still on board

    Returns
    -------
    cubes_remaining : int — updated after any delivery
    """
    if color == "GREEN":
        print("[BED] Green sticker → patient requires medication.")
        if cubes_remaining > 0:
            drop_cube(bp)
            play_delivery_sound()
            cubes_remaining -= 1
            print(f"[BED] Delivery complete. Cubes remaining: {cubes_remaining}.")
        else:
            # Edge case: robot found a green bed but has no cubes left
            print("[BED] WARNING: Green bed detected but no cubes remaining!")

    elif color == "RED":
        print("[BED] Red sticker → patient does NOT require medication. Skipping.")
        # Do NOT drop a cube — no action needed

    return cubes_remaining


# ---------------------------------------------------------------------------
# Room exit logic
# ---------------------------------------------------------------------------

def exit_room(bp):
    """
    Find the orange doorway again and drive back out to the corridor.

    Strategy:
      - Rotate slowly in place; when the color sensor detects orange,
        align the robot and drive forward through the doorway.
      - If orange is not found within EXIT_SEARCH_TIMEOUT, reverse slightly
        and try rotating the other direction (recovery behaviour).

    Parameters
    ----------
    bp : BrickPi3 instance
    """
    print("[EXIT] Searching for orange doorway...")

    # ---- Attempt 1: rotate right and look for orange ----------------------
    found_orange = _search_for_orange(bp, direction="right")

    if not found_orange:
        # Recovery: back up a little, then try rotating left instead
        print("[EXIT] Orange not found rotating right. Trying recovery...")
        drive_backward(bp, duration=0.5)
        found_orange = _search_for_orange(bp, direction="left")

    if found_orange:
        print("[EXIT] Orange doorway located. Driving through...")
        # Drive forward long enough to fully clear the doorway and be in the corridor
        drive_forward(bp, duration=EXIT_DRIVE_DURATION)
        print("[EXIT] Robot is back in the corridor.")
    else:
        # Last-resort: just drive backward (assuming the door is behind us)
        print("[EXIT] WARNING: Could not locate orange doorway. "
              "Driving backward as fallback.")
        drive_backward(bp, duration=EXIT_DRIVE_DURATION)


def _search_for_orange(bp, direction="right", timeout=None):
    """
    Rotate the robot slowly until the color sensor detects orange,
    or until the timeout expires.

    Parameters
    ----------
    bp        : BrickPi3 instance
    direction : str — "right" or "left"
    timeout   : float — seconds to search (defaults to EXIT_SEARCH_TIMEOUT)

    Returns
    -------
    bool : True if orange was found (robot stopped facing doorway), False if timed out
    """
    if timeout is None:
        timeout = EXIT_SEARCH_TIMEOUT

    deadline = time.time() + timeout

    # Start rotating in the chosen direction
    if direction == "right":
        rotate_for_exit(bp)
    else:
        # Reverse the exit-rotation motors for a left search
        bp.set_motor_dps(LEFT_MOTOR_PORT,  -EXIT_SEARCH_SPEED)
        bp.set_motor_dps(RIGHT_MOTOR_PORT,  EXIT_SEARCH_SPEED)

    while time.time() < deadline:
        color = read_color(bp)
        if color == "ORANGE":
            stop_robot(bp)
            print(f"[EXIT] Orange detected while rotating {direction}.")
            return True
        time.sleep(0.05)

    stop_robot(bp)
    return False   # Timed out without finding orange


# ---------------------------------------------------------------------------
# Main room subsystem entry point
# ---------------------------------------------------------------------------

def run_room_subsystem(bp, cubes_remaining, is_double_occupancy=False):
    """
    Full room handling sequence, called by the main navigation module
    as soon as the robot has detected the orange doorway from the corridor.

    Flow:
      [detect orange from corridor] → already handled by navigation module
          ↓
      1. Drive forward through doorway (into the room)
          ↓
      2. Sweep left-to-right for bed sticker(s)
          ↓
      3. Deliver cube to green beds / skip red beds
          ↓
      4. Locate orange doorway and exit

    Parameters
    ----------
    bp                 : BrickPi3 instance
    cubes_remaining    : int — how many cubes the robot is carrying when entering
    is_double_occupancy: bool — True if this room has two beds (affects sweep width)
                         (currently handled automatically by sweep_for_beds, but
                          you could use this flag to widen the sweep arc)

    Returns
    -------
    cubes_remaining : int — updated cube count after any deliveries in this room
    """

    room_type = "double-occupancy" if is_double_occupancy else "single"
    print(f"\n{'='*55}")
    print(f"[ROOM] Entering {room_type} patient room.")
    print(f"[ROOM] Cubes on board: {cubes_remaining}")
    print(f"{'='*55}\n")

    # ------------------------------------------------------------------
    # Step 1: Drive through the orange doorway into the room.
    # We drive far enough that the sensor is past the orange tile and
    # won't accidentally re-trigger the exit logic during the sweep.
    # ------------------------------------------------------------------
    print("[ROOM] Step 1: Crossing doorway...")
    drive_forward(bp, duration=ROOM_ENTRY_DURATION)

    # ------------------------------------------------------------------
    # Step 2 & 3: Sweep for beds and handle deliveries.
    # ------------------------------------------------------------------
    print("[ROOM] Step 2: Sweeping for bed indicators...")
    cubes_remaining = sweep_for_beds(bp, COLOR_SENSOR_PORT, cubes_remaining)

    # ------------------------------------------------------------------
    # Step 4: Find the orange doorway and exit.
    # ------------------------------------------------------------------
    print("[ROOM] Step 3: Exiting room...")
    exit_room(bp)

    print(f"\n[ROOM] Room sequence complete. Cubes remaining: {cubes_remaining}\n")
    return cubes_remaining


# ---------------------------------------------------------------------------
# BrickPi3 initialisation helper (call this once from your main script)
# ---------------------------------------------------------------------------

def init_brickpi(color_sensor_mode=None):
    """
    Initialise the BrickPi3 board and configure the color sensor.

    Parameters
    ----------
    color_sensor_mode : optional override; defaults to COLOR_COLOR_COMPONENTS
                        which returns raw RGB values for manual classification.

    Returns
    -------
    bp : BrickPi3 instance ready to use
    """
    bp = brickpi3.BrickPi3()

    # Configure the color sensor to return raw RGB + ambient components.
    # This gives us the most flexibility for custom colour classification.
    mode = color_sensor_mode or bp.SENSOR_TYPE.EV3_COLOR_COLOR_COMPONENTS
    bp.set_sensor_type(COLOR_SENSOR_PORT, mode)

    # Short delay to let the sensor initialise before we try to read from it
    time.sleep(0.5)

    print("[INIT] BrickPi3 initialised. Color sensor ready.")
    return bp


# ---------------------------------------------------------------------------
# Quick standalone test  (run: python3 room_subsystem.py)
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    """
    Standalone test: place the robot in front of an orange doorway and run this
    script to verify that the room subsystem works end-to-end.
    Remove this block or guard it further before integrating with the main script.
    """
    print("=== Room Subsystem Standalone Test ===")
    bp = init_brickpi()

    try:
        # Simulate entering a single-bed room with 2 cubes on board
        remaining = run_room_subsystem(bp, cubes_remaining=2, is_double_occupancy=False)
        print(f"Test complete. Cubes left after room: {remaining}")
    except KeyboardInterrupt:
        print("\n[TEST] Emergency stop triggered (KeyboardInterrupt).")
    finally:
        # Always reset the BrickPi before exiting to avoid motor runaway
        bp.reset_all()
        print("[TEST] BrickPi reset. Goodbye.")