#!/usr/bin/env python3

"""
 @@@@@@@  @@@ @@@@@@@  @@@@@@@  @@@@@@@@ @@@@@@@
 @@!  @@@ @@! @@!  @@@ @@!  @@@ @@!      @@!  @@@
 @!@!!@!  !!@ @!@@!@!  @!@@!@!  @!!!:!   @!@!!@!
 !!: :!!  !!: !!:      !!:      !!:      !!: :!!
  :   : : :    :        :       : :: :::  :   : :

Main loop
v2.2.0
2026-03-25
"""

# imports
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from utils.brick import BP, Motor, EV3ColorSensor, reset_brick, wait_ready_sensors, TouchSensor
import time
from multi_process_drive import Megamind
import line_follower as lf

# constants
# 1- ports
RIGHT  = "A"
LEFT   = "D"
COLOR  = EV3ColorSensor(4, mode="red")
STOP   = TouchSensor(2)
wait_ready_sensors(True)

if __name__ == "__main__":
    # REWORK BASED ON NEW MPD.PY STRUCTURE
    try:
        import titlecard
        titlecard.show()

        print("Select mode:")
        print("  1 - Manual move + rotate")
        print("  2 - Line follower")
        mode = input("Mode: ").strip()
        brain, left, right = launch_drivers(LEFT, RIGHT)

        if mode == "1":
            while not STOP.is_pressed():
                d = float(input("How far should Ripper move? (cm): "))
                brain.move(d)
                d = float(input("Turn how many degrees (algebraic): "))
                brain.rotate_in_place(d)

        elif mode == "2":
            calibrate = input("Calibrate sensor? (y/n): ").strip().lower()
            if calibrate == "y":
                white_val, black_val, orange_val = lf.calibrate(COLOR)
            else:
                white_val  = lf.DEFAULT_WHITE
                black_val  = lf.DEFAULT_BLACK
                orange_val = lf.DEFAULT_ORANGE

            duration_str = input("Run for how many seconds? (Enter for unlimited): ").strip()
            duration = float(duration_str) if duration_str else None

            lf.follow_line(LEFT, RIGHT, COLOR,
                           white_val=white_val,
                           black_val=black_val,
                           orange_val=orange_val,
                           touch=TOUCH,
                           duration=duration)
        #elif mode == "3":
        #    ts.orange_loop(LEFT, RIGHT, COLOR)
        else:
            print("Unknown mode.")

    except BaseException as e:
        print(e)
    finally:
        reset_brick()
