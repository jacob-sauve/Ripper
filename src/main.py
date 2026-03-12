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
from .. import utils
from utils.brick import BP, Motor, reset_brick
import time
import drive as ts

# constants
# 1- ports
RIGHT = Motor("A")
LEFT = Motor("D")


if __name__ == "__main__":
    # main loop
    try:
        import titlecard
        print("You are now piloting...\n\n")
        titlecard.show()
        d = float(input("How far should Ripper move? (cm): "))
        ts.move(LEFT, RIGHT, d)
        d = float(input("Turn how many degrees (algebraic): "))
        ts.rotate_in_place(LEFT, RIGHT, d)
    except BaseException as e:
        print(e)
    finally:
        reset_brick()
