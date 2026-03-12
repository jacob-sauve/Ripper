#!/usr/bin/env python3

"""
 @@@@@@@  @@@ @@@@@@@  @@@@@@@  @@@@@@@@ @@@@@@@
 @@!  @@@ @@! @@!  @@@ @@!  @@@ @@!      @@!  @@@
 @!@!!@!  !!@ @!@@!@!  @!@@!@!  @!!!:!   @!@!!@!
 !!: :!!  !!: !!:      !!:      !!:      !!: :!!
  :   : : :    :        :       : :: :::  :   : :

Main loop
v0.1.5
2026-03-12
"""

# imports
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from utils.brick import BP, Motor, EV3ColorSensor, reset_brick
import time
import drive as ts
import line_follower as lf

# constants
# 1- ports
RIGHT  = Motor("A")
LEFT   = Motor("D")
COLOR  = EV3ColorSensor(1, mode="red")  # color sensor on port 1


if __name__ == "__main__":
    try:
        import titlecard
        print("You are now piloting...\n\n")
        titlecard.show()

        print("Select mode:")
        print("  1 - Manual move + rotate")
        print("  2 - Line follower")
        mode = input("Mode: ").strip()

        if mode == "1":
            d = float(input("How far should Ripper move? (cm): "))
            ts.move(LEFT, RIGHT, d)
            d = float(input("Turn how many degrees (algebraic): "))
            ts.rotate_in_place(LEFT, RIGHT, d)

        elif mode == "2":
            calibrate = input("Calibrate sensor? (y/n): ").strip().lower()
            if calibrate == "y":
                white_val, black_val = lf.calibrate(COLOR)
            else:
                white_val, black_val = lf.DEFAULT_WHITE, lf.DEFAULT_BLACK

            duration_str = input("Run for how many seconds? (Enter for unlimited): ").strip()
            duration = float(duration_str) if duration_str else None

            lf.follow_line(LEFT, RIGHT, COLOR,
                           white_val=white_val,
                           black_val=black_val,
                           duration=duration)
        else:
            print("Unknown mode.")

    except BaseException as e:
        print(e)
    finally:
        reset_brick()
