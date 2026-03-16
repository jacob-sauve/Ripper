#!/usr/bin/env python3

"""
Ripper driving scripts.
Implemented using multiprocessing.
"""

# imports
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from utils.brick import BP, Motor, reset_brick
from vision import _read_rgb, is_orange
import math
import time
from multiprocess import cpu_count, Process


# constants
R_WHEEL = 2.2       # wheel radius in cm
R_ROBOT = 7.60      # middle wheel to middle wheel in cm
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

def orange_loop(left, right, color, speed=MIN_SPEED):
    while True:
        left.set_dps(-speed)
        right.set_dps(-speed)
        r,g,b = _read_rgb(color)
        while not (is_orange(r,g,b)):
            time.sleep(0.1)
            r,g,b = _read_rgb(color)
        left.set_dps(0)
        right.set_dps(0)
        rotate_in_place(left, right, 180, speed)


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

def 


# main loop
if __name__ == "__main__":
    try:
        import titlecard
        titlecard.show()
        print(f"{cpu_count()=}")
    except BaseException as e:
        print(e)
    finally:
        reset_brick()
