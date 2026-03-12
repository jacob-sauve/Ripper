#!/usr/bin/env python3

"""
Ripper test scripts.
"""

# imports
from utils.brick import BP, Motor, reset_brick
import time

# constants


def drive_test(right, left):
    print("moving...")
    right.set_dps(20)
    left.set_dps(20)
    time.sleep(5)
    print("moved!")
