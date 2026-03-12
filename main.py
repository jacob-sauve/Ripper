#!/usr/bin/env python3

"""
 @@@@@@@  @@@ @@@@@@@  @@@@@@@  @@@@@@@@ @@@@@@@
 @@!  @@@ @@! @@!  @@@ @@!  @@@ @@!      @@!  @@@
 @!@!!@!  !!@ @!@@!@!  @!@@!@!  @!!!:!   @!@!!@!
 !!: :!!  !!: !!:      !!:      !!:      !!: :!!
  :   : : :    :        :       : :: :::  :   : :

Main loop
v0.1.3
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
        import titlecard
        print("You are now piloting...")
        titlecard.show()
        d = int(input("How far should Ripper move? (cm): "))
        ts.move(LEFT, RIGHT, d)
    except BaseException as e:
        print(e)
    finally:
        reset_brick()
