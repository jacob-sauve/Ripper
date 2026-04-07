#!/usr/bin/env python3

"""
 @@@@@@@  @@@ @@@@@@@  @@@@@@@  @@@@@@@@ @@@@@@@
 @@!  @@@ @@! @@!  @@@ @@!  @@@ @@!      @@!  @@@
 @!@!!@!  !!@ @!@@!@!  @!@@!@!  @!!!:!   @!@!!@!
 !!: :!!  !!: !!:      !!:      !!:      !!: :!!
  :   : : :    :        :       : :: :::  :   : :

Main loop
v2.5.0
2026-04-02
"""

# imports
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from utils.brick import BP, Motor, EV3ColorSensor, reset_brick, wait_ready_sensors, TouchSensor
from time import sleep
from multi_process_drive import Megamind, Vision, Driver
from command_parser import parse_commandfile

# constants
# N/A


if __name__ == "__main__":
    processors = {
            "GYRO": Vision("GYRO", 3, 0.01),
            "LEFT": Driver("LEFT", "A"),
            "RIGHT": Driver("RIGHT", "D"),
            "GRABBER": Driver("GRABBER", "B"),
            "SWEEPER": Driver("SWEEPER", "C"),
            "COLOR": Vision("COLOR", 1, 0.01)
            }
    brain = Megamind(processors)
    stop = TouchSensor(2)

    try:
        import titlecard
        titlecard.show()
        
        # get commands from file
        commands = parse_commandfile("commands.txt", brain.funcdict, debug=True)
        for command in commands:
            brain.queue.put_nowait(command)

        # main loop (emergency stop)
        while not stop.is_pressed():
            sleep(0.01)
        raise Exception()

    except BaseException as e:
        print(e)
    finally:
        print("killing...")
        brain.killAll()
        print("killed.")
        reset_brick()
