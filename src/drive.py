#!/usr/bin/env python3

"""
Ripper driving scripts.
"""

# imports
from utils.brick import BP, Motor, reset_brick
import math
import time

# constants
R_WHEEL = 2.2       # wheel radius in cm
R_ROBOT = 7.55      # middle wheel to middle wheel in cm
MIN_SPEED = 270     # wheel rotation speed in degrees.s-1


def move(left, right, distance, speed=MIN_SPEED):
    n_rotations = abs(distance/(R_WHEEL * math.pi * 2))
    spin_time = (n_rotations*360)/speed
    if distance < 0:
        direction = 1
    else:
        direction = -1
    left.set_dps(direction * speed)
    right.set_dps(direction * speed)
    time.sleep(spin_time)
    left.set_dps(0)
    right.set_dps(0)


def rotate_in_place(left, right, degrees, speed=MIN_SPEED):
    distance = R_ROBOT * (degrees * math.pi / 180)
    # divide by 2 to find rotation distance per wheel
    n_rotations = (abs(distance/(R_WHEEL * math.pi * 2)))
    spin_time = (n_rotations*360)/speed
    if degrees < 0:
        direction = 1
    else:
        direction = -1
    left.set_dps(direction * speed)
    right.set_dps(-direction * speed)
    time.sleep(spin_time)
    left.set_dps(0)
    right.set_dps(0)


# main loop
if __name__ == "__main__":
    try:
        import titlecard
        titlecard.show()
    except BaseException as e:
        print(e)
    finally:
        reset_brick()
