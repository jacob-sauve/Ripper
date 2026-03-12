#!/usr/bin/env python3

"""
Displays ripper titlecard
"""

# imports
from utils.brick import BP, Motor, reset_brick

# constants
RIPPER = r"""@@@@@@@   @@@  @@@@@@@   @@@@@@@   @@@@@@@@  @@@@@@@
@@@@@@@@  @@@  @@@@@@@@  @@@@@@@@  @@@@@@@@  @@@@@@@@
@@!  @@@  @@!  @@!  @@@  @@!  @@@  @@!       @@!  @@@
!@!  @!@  !@!  !@!  @!@  !@!  @!@  !@!       !@!  @!@
@!@!!@!   !!@  @!@@!@!   @!@@!@!   @!!!:!    @!@!!@!
!!@!@!    !!!  !!@!!!    !!@!!!    !!!!!:    !!@!@!
!!: :!!   !!:  !!:       !!:       !!:       !!: :!!
:!:  !:!  :!:  :!:       :!:       :!:       :!:  !:!
::   :::   ::   ::        ::        :: ::::  ::   :::
 :   : :  :     :         :        : :: ::    :   : :
"""


def show():
    print(RIPPER)



# main loop
if __name__ == "__main__":
    try:
        show()
    except BaseException as e:
        print(e)
    finally:
        reset_brick()
