#!/usr/bin/env python3

"""
 @@@@@@@  @@@ @@@@@@@  @@@@@@@  @@@@@@@@ @@@@@@@
 @@!  @@@ @@! @@!  @@@ @@!  @@@ @@!      @@!  @@@
 @!@!!@!  !!@ @!@@!@!  @!@@!@!  @!!!:!   @!@!!@!
 !!: :!!  !!: !!:      !!:      !!:      !!: :!!
  :   : : :    :        :       : :: :::  :   : :

Main loop
v2.4.0
2026-04-01
"""

# imports
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from utils.brick import BP, Motor, EV3ColorSensor, reset_brick, wait_ready_sensors, TouchSensor
import time
from multi_process_drive import Megamind
import line_follower as lf

# constants
# 1- ports
RIGHT  = "A"
LEFT   = "D"
COLOR  = EV3ColorSensor(4, mode="red")
STOP   = TouchSensor(2)
wait_ready_sensors(True)

if __name__ == "__main__":
    processors = {
            "GYRO": Vision("GYRO", 3, 0.01),
            "LEFT": Driver("LEFT", "D"),
            "RIGHT": Driver("RIGHT", "A"),
            "GRABBER": Driver("GRABBER", "B"),
            "SWEEPER": Driver("SWEEPER", "C"),
            "COLOR": Vision("COLOR", 1)
            }
    brain = Megamind(processors)
    stop = TouchSensor(2)

    try:
        import titlecard
        titlecard.show()
        print(f"{cpu_count()=}\n\n")
        with open("commands.txt", "rt") as f:
            lines = f.read()
        commands = lines.splitlines()

        for command, *args in commands:
            check = len(args) == len(list(filter(lambda x: x.isdecimal(), args)))
            if (not command.upper() in brain.funcdict) or (not check):
                print(f"Invalid command: {command}")
            else:
                print(f"Executing command: {command}")
                brain.queue.put_nowait((command.upper(), *list(map(int, args))))

    except BaseException as e:
        print(e)
    finally:
        print("killing...")
        brain.killAll()
        print("killed.")
        reset_brick()
