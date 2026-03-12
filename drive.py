#!/usr/bin/env python3

"""
Ripper driving scripts.
"""

# imports
from utils.brick import BP, Motor, reset_brick
import math
import time

# constants
R_WHEEL = 10        # wheel radius in cm
MIN_SPEED = 90      # wheel rotation speed in degrees.s-1

def move(left, right, distance, speed=MIN_SPEED):
    n_rotations = distance/(R_WHEEL * math.pi * 2)
    spin_time = (n_rotations*360)/speed
    left.dps(speed)
    right.dps(speed)
    time.sleep(spin_time)


# main loop
if __name__ == "__main__":
    try:
        import titlecard
        titlecard.show()
    except BaseException as e:
        print(e)
    finally:
        reset_brick()
