#!/usr/bin/env python3

"""
Displays ripper titlecard
"""

# imports

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
    print("\n\n\033[3mYou are now piloting...\033[0m\n\n")
    print(RIPPER)



# main loop
if __name__ == "__main__":
    try:
        show()
    except BaseException as e:
        print(e)
    finally:
        pass
