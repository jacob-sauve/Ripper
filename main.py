#!/usr/bin/env python3

"""
 @@@@@@@  @@@ @@@@@@@  @@@@@@@  @@@@@@@@ @@@@@@@
 @@!  @@@ @@! @@!  @@@ @@!  @@@ @@!      @@!  @@@
 @!@!!@!  !!@ @!@@!@!  @!@@!@!  @!!!:!   @!@!!@!
 !!: :!!  !!: !!:      !!:      !!:      !!: :!!
  :   : : :    :        :       : :: :::  :   : :

Main loop
v0.1.2
2026-03-12
"""

# imports
from utils.brick import BP, Motor, reset_brick
import time
import test_scripts as ts

# constants
# 1- ports
RIGHT = Motor("A")
LEFT = Motor("D")


if __name__ == "__main__":
    # main loop
    try:
        right.set_dps(20)
        left.set_dps(20)
        time.sleep(5)
    except BaseException as e:
        print(e)
    finally:
        reset_brick()
