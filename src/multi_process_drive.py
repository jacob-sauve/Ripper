#!/usr/bin/env python3

"""
Ripper driving scripts.
Implemented using multiprocessing.
"""

# imports
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from utils.brick import reset_brick, Motor
from vision import _read_rgb, is_orange
import math
import time
from multiprocess import cpu_count, Process, Queue


# constants
R_WHEEL = 2.2       # wheel radius in cm
R_ROBOT = 7.60      # middle wheel to middle wheel in cm
MIN_SPEED = 270     # wheel rotation speed in degrees.s-1
LEFT = 1            # multiplier for correct rotations of left wheel
RIGHT = -1          # multiplier for correct rotations of right wheel

class Megamind:
    """
    Dispatcher/controller
    Reads main instruction queue and sends instructions to each wheel
    ⢘⣾⣾⣿⣾⣽⣯⣼⣿⣿⣴⣽⣿⣽⣭⣿⣿⣿⣿⣿⣧
⠀⠀⠀⣾⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿
⠀⠀⠠⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿
⠀⠀⣰⣯⣾⣿⣿⡼⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⡿
⠀⠀⠛⠛⠋⠁⣠⡼⡙⢿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⡿⠁
⠀⠀⠀⠤⣶⣾⣿⣿⣿⣦⡈⠉⠉⠉⠙⠻⣿⣿⣿⣿⣿⠿⠁⠀
⠀⠀⠀⠀⠈⠟⠻⢛⣿⣿⣿⣷⣶⣦⣄⠀⠸⣿⣿⣿⠗⠀⠀⠀
⠀⠀⠀⠀⠀⣼⠀⠄⣿⡿⠋⣉⠈⠙⢿⣿⣦⣿⠏⡠⠂⠀⠀⠀
⠀⠀⠀⠀⢰⡌⠀⢠⠏⠇⢸⡇⠐⠀⡄⣿⣿⣃⠈⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠈⣻⣿⢫⢻⡆⡀⠁⠀⢈⣾⣿⠏⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⢀⣿⣻⣷⣾⣿⣿⣷⢾⣽⢭⣍⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⣼⣿⣿⣿⣿⡿⠈⣹⣾⣿⡞⠐⠁⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠨⣟⣿⢟⣯⣶⣿⣆⣘⣿⡟⠁⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⡆⠀⠐⠶⠮⡹⣸⡟⠁⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
    """
    def __init__(self, queue, left_queue, right_queue):
        self.left_queue = left_queue
        self.right_queue = right_queue
        self.queue = queue
        self.process = Process(target=self.parse_instructions)
        self.process.start()

    def move(self, distance, speed=MIN_SPEED):
        self.queue.put(("GO", distance, speed))

    def rotate_in_place(self, degrees, speed=MIN_SPEED):
        self.queue.put(("TURN", degrees, speed))

    def parse_instructions(self):
        while True:
            instruction = self.queue.get()
            if instruction:
                self.left_queue.put(instruction)
                self.right_queue.put(instruction)


class Driver:
    """One driver per motor; worker class for process management"""
    def __init__(self, motor_pin_name, direction, queue, min_speed=MIN_SPEED):
        self.motor_pin = Motor(motor_pin_name)
        self.direction = direction
        self.process = Process(target = self.driver_loop)
        self.queue = queue
        self.min_speed = min_speed
        # dict mapping funcnames to funcs for safe pickling
        self.funcdict = {
                "TURN": self._turn,
                "GO": self._go
                }
        self.process.start()

    def _turn(self, degrees, speed=None):
        """rotate a given number of degrees"""
        # set default speed value
        print(f"turning {degrees} degrees...")
        speed = speed if speed is not None else self.min_speed
        distance = R_ROBOT * (degrees * math.pi / 180)
        n_rotations = (abs(distance/(R_WHEEL * math.pi * 2)))
        spin_time = (n_rotations*360)/speed
        if degrees < 0:
            direction = 1 * self.direction
        else:
            direction = -1 * self.direction
        self.motor_pin.set_dps(direction * speed)
        time.sleep(spin_time)
        self.motor_pin.set_dps(0)
        print("turned!")

    def _go(self, distance, speed=None):
        """roll wheel over a given distance in cm"""
        print("moving wheel {distance} cm...")
        speed = speed if speed is not None else self.min_speed
        n_rotations = abs(distance/(R_WHEEL * math.pi * 2))
        spin_time = (n_rotations*360)/speed
        if distance < 0:
            direction = 1
        else:
            direction = -1
        self.motor_pin.set_dps(direction * speed)
        time.sleep(spin_time)
        self.motor_pin.set_dps(0)
        print("moved!")

    def driver_loop(self):
        while True:
            instruction = self.queue.get()
            if instruction:
                funcname, *args = instruction
                self.funcdict[funcname](*args)


def launch_drivers(left_pin, right_pin):
    # overarching queue used by dispatcher
    papa_queue = Queue()
    # subqueues per motor
    left_queue = Queue()
    right_queue = Queue()
    # drivers for each wheel
    left = Driver(left_pin, LEFT, left_queue)
    right = Driver(right_pin, RIGHT, right_queue)
    # dispatcher who sends specific instructions from general ones received
    brain = Megamind(papa_queue, left_queue, right_queue)
    return brain, left, right


def killall(brain, left, right):
    """stop all active processes"""
    for processor in brain, left, right:
        try:
            processor.process.join()
        except:
            pass


# main loop
if __name__ == "__main__":
    try:
        brain, left, right = launch_drivers("A", "D")
    except Exception as e:
        print(e)
        killall(brain, left, right)
        raise Exception("unable to launch driver processes")
    try:
        import titlecard
        titlecard.show()
        print(f"{cpu_count()=}\n\n")
        brain.move(20)
        brain.rotate_in_place(180)
        brain.move(20)
        brain.rotate_in_place(180)
        killall(brain, left, right)
    except BaseException as e:
        print(e)
    finally:
        killall(brain, left, right)
        reset_brick()
