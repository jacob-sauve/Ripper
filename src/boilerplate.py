#!/usr/bin/env python3

"""
Ripper scripts.
"""

# imports
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from utils.brick import BP, Motor, reset_brick

# constants


# main loop
if __name__ == "__main__":
    try:
        import titlecard
        titlecard.show()
    except BaseException as e:
        print(e)
    finally:
        reset_brick()
