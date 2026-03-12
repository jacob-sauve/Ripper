#!/usr/bin/env python3

"""
Ripper test scripts.
"""

# imports
from utils.brick import BP, Motor, reset_brick
import time
import drive

# constants


def move(left, right distance):
    print("moving...")
    drive.move(left, right, distance)
    print("moved!")
