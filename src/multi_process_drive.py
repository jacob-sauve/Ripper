#!/usr/bin/env python3

"""
Ripper driving scripts.
Implemented using multiprocessing.
"""

# imports
import sys
import os
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from utils.brick import reset_brick, Motor, EV3ColorSensor, EV3GyroSensor, TouchSensor, wait_ready_sensors
from math import pi
from time import sleep
from multiprocess import cpu_count, Process, Queue
from colors import classify
from musical import victor_jingle, delivery_jingle


# constants
DIRECTION = 1           # defines which way is forward versus backwards (e.g. -1 means negative speed --> forward motion)
R_GRABBER = 1.8         # grabber motor turn radius in cm
R_WHEEL = 2.2           # wheel radius in cm
R_ROBOT = 7.52          # middle wheel to middle wheel in cm
MIN_SPEED = 270         # wheel rotation speed in degrees.s-1
GRABBER = -1            # multiplier for correct rotations of grabber (should be pickup direction)
SWEEPER = +1            # multiplier for correct rotations of front-mounted colour sensor sweep motor
MEGAMIND_BUFFER = 0.005 # seconds between Megamind queue parsings
MAX_DRIFT = 0.5         # max degrees of drift acceptable from desired rectilinear trajectory
DRIFT_CORRECTION = 1.15 # percentage (decimal form) of desired speed applied to lagging wheel if drifting
BED_LENGTH = 12         # length of a bed in centimeters
START_SWEEP_ANGLE = 0   # initial angle of sweeper
SWEEP_MINIMUM_TURN = 5  # degrees of smallest sweep increment
START_DIRECTION = 0     # degrees of orientation at the beginning when placed in pharmacy (decide on convention)
MAX_ROOM_DISTANCE = 90  # centimeters of straight-line motion before robot can safely assume it is in a room
SWEEPS_PER_SWEEP = 2    # number of full ROMs swept per call of Megamind._sweep()
FW_PER_SWEEP = 10       # centimeters of straight-line motion between every sweep


def safeGet(queue):
    """Get from queue wrapped in empty check, None if empty
    returns the method that will be called in future
    """
    return lambda wait: queue.get(wait) if not queue.empty() else None


class Processor:
    """Parent class for all process wrapper classes"""
    def __init__(self, name):
        self.queue = Queue()                                # queue for interprocess comms through Megamind
        self.name = name
        self.process = Process(target=self.manage_queue)    # start process with queue parsing loop

    def start(self):
        # add safeGet method at RunTime
        self.queue.safeGet = safeGet(self.queue)
        self.process.start()

    def manage_queue(self):
        # implemented differently for actuators (get from queue) and sensors (put)
        pass


class Megamind(Processor):
    """
    Dispatcher/controller
    Reads main instruction queue and
        L-> sends instructions to motors
        L-> polls sensors
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
    def __init__(self, processor_dict=dict()):
        super().__init__("MEGAMIND")
        self.is_busy = False
        self.active_command = None
        # dictionnary mapping processor (sensor or actuator) name to Processor object
        self.processor_dict = processor_dict
        self.funcdict = {
                "GO": self._go_with_sensors,
                "TURN": self._turn_with_sensors,
                "GRAB": self._grab,
                "SWEEP": self._sweep,
                "JINGLE": victor_jingle,
                "GO_DOOR": self._go_to_door

                }
        # mapping of Sensor objects to their respective most recent readings
        self.latest_readings = dict()
        self.initial_orientation = None # for calibration of direction over multiple func calls
        # to keep track of where we WANT to be facing
        self.current_direction = START_DIRECTION # for DESIRED direction, NOT true direction
        self.start()

    def start(self):
        wait_ready_sensors(True)
        # to prevent compound microdrifts if correction doesn't manage to complete itself in time
        # include wait to let sensors initialise
        try:
            self.initial_orientation = self.clearSensorQueues(wait=True).get("GYRO").get("angle")
        except:
            pass
        finally:
            super().start()

    def addProcessor(self, processor):
        """connect a new processor (sensor/actuator)"""
        if processor is None:
            return False
        self.processor_dict[processor.name] = processor
        print(self.processor_dict)
        return True


    def killProcessor(self, processor):
        """kill processor object passed as arg"""
        if processor is None:
            return False
        processor.process.terminate() # kill active process
        return True

    def killProcessorByName(self, name):
        processor = self.processor_dict.get(name)
        return self.killProcessor(processor)

    def killAll(self):
        for name in self.processor_dict:
            self.killProcessorByName(name)
        # kill itself
        self.process.terminate()


    def clearSensorQueues(self, wait = False):
        """Empty all sensor queues to have up-to-date data at front of queue"""
        sensors = (self.processor_dict.get("GYRO"),
                   self.processor_dict.get("COLOR"))
        queue_front_dict = dict(zip(sensors, [None]*len(sensors)))
        for sensor in sensors:
            if not (sensor is None):
                try:
                    queue_front = sensor.queue.safeGet(wait)
                #queue_front = sensor.queue.safeGet()
                except:
                    queue_front = None
                while not (sensor.queue.empty()):
                    queue_front_dict[sensor] = queue_front
                    queue_front = sensor.queue.safeGet(wait)
        return queue_front_dict

    def manage_queue(self):
        """probably should rework --> could easily get stuck in busy mode"""
        while True: 
            instruction = self.queue.safeGet(False)
            if instruction:
                print(instruction)
                funcname, args = instruction[0], instruction[1:]
                self.funcdict[funcname](*args)
            # clear sensor queues to keep them up to date, store newest readings
            self.latest_readings = self.clearSensorQueues()
            sleep(MEGAMIND_BUFFER)

    def _distance_to_iterations(self, distance, speed=MIN_SPEED, radius=R_WHEEL):
        # calculate how much motor rotation is necessary to move distance
        n_rotations = abs(distance / (radius * pi * 2))
        spin_time = (n_rotations * 360) / speed
        # calculate amount of iterations with delay equal to constant buffer are needed
        return int(abs(spin_time / MEGAMIND_BUFFER))

    def _degrees_to_iterations(self, degrees, speed=MIN_SPEED):
        spin_time = degrees / speed
        return int(abs(spin_time/MEGAMIND_BUFFER))

    def _go_with_sensors(self, distance, speed=MIN_SPEED):
        """go a certain distance in a straight line. uses gyro for drift mgmt."""
        granular_iterations = self._distance_to_iterations(distance, speed)
        left, right, gyro = (self.processor_dict.get("LEFT"),
                             self.processor_dict.get("RIGHT"),
                             self.processor_dict.get("GYRO"))
        # account for way the wheels are mounted when determining what is fw/bw
        speed = DIRECTION * speed
        left.queue.put(("GO", speed))
        right.queue.put(("GO", speed))
        # get most recent gyro reading, if existent
        # take it as reference for "straightness"
        if not (self.initial_orientation is None):
            initial_angle = self.initial_orientation + self.current_direction
        else:
            initial_angle = gyro.queue.safeGet(True).get("angle")
        for i in range(granular_iterations):
            gyro_readings = gyro.queue.safeGet(False)
            if gyro_readings:
                drift =  gyro_readings.get("angle") - initial_angle
                # flip these corrections if they're inverted
                #print(f"{drift=}")
                if (drift > MAX_DRIFT and speed < 0) or (drift < -MAX_DRIFT and speed > 0):
                    # NEW LEFT DRIFT
                    print("left drift. correcting...")
                    # left wheel lagging
                    #right.queue.put(("STOP",))
                    #left.queue.put(("STOP",))
                    right.queue.put(("GO", speed / DRIFT_CORRECTION))
                    left.queue.put(("GO", speed * DRIFT_CORRECTION))
                    #right.queue.put(("STOP",))
                    #left.queue.put(("GO", speed))

                elif (drift < -MAX_DRIFT and speed < 0) or (drift > MAX_DRIFT and speed > 0):
                    # NEW RIGHT DRIFT
                    print("right drift. correcting...")
                    # right wheel lagging
                    #right.queue.put(("STOP",))
                    #left.queue.put(("STOP",))
                    right.queue.put(("GO", speed * DRIFT_CORRECTION))
                    left.queue.put(("GO", speed / DRIFT_CORRECTION))
                    #right.queue.put(("GO", speed))
                    #left.queue.put(("STOP",))

                else:
                    # all good
                    left.queue.put(("GO", speed))
                    right.queue.put(("GO", speed))
            #print("about to sleep, iterating...")
            sleep(MEGAMIND_BUFFER)
        left.queue.put(("STOP",))
        right.queue.put(("STOP",))
        return True

    def _turn_with_sensors(self, degrees, speed=MIN_SPEED):
        left, right, gyro = (self.processor_dict.get("LEFT"),
                             self.processor_dict.get("RIGHT"),
                             self.processor_dict.get("GYRO"))
        gyro_readings = gyro.queue.safeGet(True)
        
        direction = DIRECTION if degrees > 0 else -DIRECTION
        target_angle = self.current_direction + degrees # gyro does not mod by 360
        curr_angle = gyro_readings.get("angle")
        while (curr_angle != target_angle):
            gyro_readings = gyro.queue.safeGet(False)
            if not (gyro_readings is None):
                curr_angle = gyro_readings.get("angle")
            if (abs(curr_angle - target_angle) < 15) and speed > 110:
                speed = speed * .8
            left.queue.put(("GO", direction * speed))
            right.queue.put(("GO", -direction * speed))
            sleep(MEGAMIND_BUFFER)
            print(f"{gyro_readings=}")
        print(f"stopped turning, final gyro reading: {gyro_readings}")
        self.current_direction = gyro_readings.get("angle")
        left.queue.put(("STOP",))
        right.queue.put(("STOP",))
        return True

    def _grab(self, distance, speed=MIN_SPEED):
        granular_iterations = self._distance_to_iterations(distance, radius=R_GRABBER)
        grabber = self.processor_dict.get("GRABBER")

        grabber.queue.put(("GO", speed))

        for i in range(granular_iterations):
            print(f"waiting... iteration {i}")
            sleep(MEGAMIND_BUFFER)

        grabber.queue.put(("STOP",))
        return True

    def _sweep(self, range_of_motion, center=True, speed=MIN_SPEED):
        #granular_iterations = self._degrees_to_iterations(degrees, speed)
        sweeper, color = (self.processor_dict.get("SWEEPER"), self.processor_dict.get("COLOR"))

        if center:
            start = START_SWEEP_ANGLE - range_of_motion // 2
        else:
            start = START_SWEEP_ANGLE
        # set start angle 
        sweeper.queue.put(("ANGLE", start-START_SWEEP_ANGLE, speed))
        increment = SWEEP_MINIMUM_TURN
        for i in range(SWEEPS_PER_SWEEP):
            for degrees in range(start, range_of_motion + start, increment):
                sweeper.queue.put(("ANGLE", degrees, speed))
                sleep(MEGAMIND_BUFFER*2)
                color_readings = color.queue.safeGet(False)
                if color_readings:
                    curr_color = color_readings.get("color")
                    print(f"{color_readings.get('rgb') = }")
                    if curr_color == "green":
                        # play happy sounds if patient found
                        sweeper.queue.put(("STOP",))
                        self.queue.put(("JINGLE",))
                        return True
                    elif curr_color == "red":
                        # exit room if patient invalid
                        sweeper.queue.put(("STOP",))
                        self.queue.put(("GO", 10, -MIN_SPEED))
                        self.queue.put(("GO_DOOR", -MIN_SPEED))
                        return True
            sleep(MEGAMIND_BUFFER*20)
            start *= -1
            range_of_motion *= -1
            increment *= -1
        #turn(degrees)
        #forward(5cm)
        #grabber(-speed)
        #backward(5cm)
        #turn(-degrees)
        #return
        # false if not found
        # queue instructions again
        self.queue.put(("GO", FW_PER_SWEEP, MIN_SPEED))
        self.queue.put(("SWEEP", range_of_motion, center, speed))
        sleep(0.5)
        return False

    def _go_to_door(self, speed=MIN_SPEED):
        """advance until orange is detected; then proceed to room logic"""
        granular_iterations = self._distance_to_iterations(MAX_ROOM_DISTANCE, speed)
        left, right, gyro, color = (self.processor_dict.get("LEFT"),
                                    self.processor_dict.get("RIGHT"),
                                    self.processor_dict.get("GYRO"),
                                    self.processor_dict.get("COLOR"))
        speed = DIRECTION * speed
        left.queue.put(("GO", speed))
        right.queue.put(("GO", speed))
        # get most recent gyro reading, if existent
        # take it as reference for "straightness"
        print("go to door protocol initiated")
        print(f"{granular_iterations = }")
        if not (self.initial_orientation is None):
            initial_angle = self.initial_orientation + self.current_direction
        else:
            initial_angle = gyro.queue.safeGet(False).get("angle")
        for i in range(granular_iterations):
            gyro_readings = gyro.queue.safeGet(False)
            print(f"{gyro_readings=}")
            color_readings = color.queue.safeGet(False)
            if color_readings:
                curr_color = color_readings.get("color")
                if curr_color and curr_color == "orange":
                    break
            if gyro_readings:
                drift =  gyro_readings.get("angle") - initial_angle
                print(f"{drift=}")
                # flip these corrections if they're inverted
                #print(f"{drift=}")
                if (drift > MAX_DRIFT and speed < 0) or (drift < -MAX_DRIFT and speed > 0):
                    # NEW LEFT DRIFT

                    print("left drift. correcting...")
                    # left wheel lagging
                    #right.queue.put(("STOP",))
                    #left.queue.put(("STOP",))
                    right.queue.put(("GO", speed / DRIFT_CORRECTION))
                    left.queue.put(("GO", speed * DRIFT_CORRECTION))
                    #right.queue.put(("STOP",))
                    #left.queue.put(("GO", speed))

                elif (drift < -MAX_DRIFT and speed < 0) or (drift > MAX_DRIFT and speed > 0):
                    # NEW RIGHT DRIFT
                    print("right drift. correcting...")
                 # right wheel lagging
                    #right.queue.put(("STOP",))
                    #left.queue.put(("STOP",))
                    right.queue.put(("GO", speed * DRIFT_CORRECTION))
                    left.queue.put(("GO", speed / DRIFT_CORRECTION))
                    #right.queue.put(("GO", speed))
                    #left.queue.put(("STOP",))
                else:
                    # all good
                    left.queue.put(("GO", speed))
                    right.queue.put(("GO", speed))
            #print("about to sleep, iterating...")
            sleep(MEGAMIND_BUFFER)
        left.queue.put(("STOP",))
        right.queue.put(("STOP",))
        return True






class Driver(Processor):
    """One driver per motor; worker class for process management"""
    def __init__(self, name, motor_pin_name, min_speed=MIN_SPEED):
        self.motor_pin_name = motor_pin_name
        self.is_moving = False
        # dict mapping funcnames to funcs for safe pickling
        self.funcdict = {
                "GO": self._go,
                "STOP": self._stop,
                "ANGLE": self._angle
                }
        self.name = name.upper()
        if self.name == "LEFT":
            self.direction = DIRECTION
        elif self.name == "RIGHT":
            self.direction = DIRECTION
        elif self.name == "GRABBER":
            # grabber
            self.direction = GRABBER
        elif self.name == "SWEEPER":
            # sweeper colour sensor
            self.direction = SWEEPER
        else:
            raise ValueError(f"Invalid Motor name: '{self.name}'. Should be one of: 'LEFT', 'RIGHT', 'GRABBER'")
        self.min_speed = min_speed * self.direction
        super().__init__(self.name)
        self.start()

    def start(self):
        """Start process, initialise Motor output pin"""
        self.motor_pin = Motor(self.motor_pin_name)
        super().start()

    def _go(self, speed=None):
        """start moving"""
        # set default speed value
        speed = self.direction*speed if speed is not None else self.min_speed
        self.motor_pin.set_limits(dps=speed)
        try:
            power = 100*(self.direction * speed)/self.motor_pin.MAX_SPEED
            #print(power)
            self.motor_pin.set_power(power)
            self.is_moving = True
           #print(self.name + " moving")
            return True
        except:
            return False

    def _angle(self, degrees, speed=None):
        """face a certain angle""" 
        # limit speed
        speed = self.direction*speed if speed is not None else self.min_speed
        self.motor_pin.set_limits(dps=speed)
        # turn!
        self.motor_pin.set_position(degrees)

    def _stop(self):
        """stop moving"""
        try:
            print("stopping...")
            self.motor_pin.set_power(0)
            self.is_moving = False
            print("stopped")
            return True
        except:
            return False

    def manage_queue(self):
        while True:
            instruction = self.queue.safeGet(False)
            if instruction:
                funcname, args = instruction[0], instruction[1:]
                self.funcdict[funcname](*args)


class Vision(Processor):
    """One Vision object per sensor; worker class for process management"""
    def __init__(self, name, sensor_pin_number, poll_period=MEGAMIND_BUFFER):
        self.sensor_pin_number = sensor_pin_number
        self.name = name.upper()
        # seconds between sensor polls
        self.poll_period = poll_period
        # set port initialisation and polling functions
        if self.name == "GYRO":
            self.setup_function = EV3GyroSensor
            self.read = self.gyro_measure
        elif self.name == "TOUCH":
            self.setup_function = TouchSensor
            self.read = self.touch_measure
        elif self.name == "COLOR":
            self.setup_function = EV3ColorSensor
            self.read = self.color_measure
        else:
            raise ValueError(f"Invalid Sensor name: '{self.name}'. Should be one of: 'GYRO', 'TOUCH', 'COLOR'")
        super().__init__(self.name)
        self.start()

    def start(self):
        # setup sensor pin
        self.sensor_pin = self.setup_function(self.sensor_pin_number)
        super().start()

    def gyro_measure(self, *args):
        if self.name != "GYRO":
            return False
        data = self.sensor_pin.get_both_measure()
        if data is None:
            return None
        output = dict()
        for mode in args:
            if mode == "angle":
                output["angle"] = data[0]
            if mode == "dps":
                output["dps"] = data[1]
        print(f"{output}")
        return output

    def touch_measure(self, *args):
        if self.name != "TOUCH":
            return False
        is_pressed = self.sensor_pin.is_pressed()
        if is_pressed:
            return {"press":is_pressed}

    def color_measure(self, *args):
        sleep(0.01)
        if self.name != "COLOR":
            return False
        rgb = self.sensor_pin.get_rgb()
        output = dict()
        if rgb != None and not None in rgb:
            color = classify(rgb, debugging=False) # SET TO TRUE FOR CALIBRATION
            output["color"] = color
            output["rgb"] = rgb
        return output

    def manage_queue(self):
        while True:
            args = []
            if self.name == "GYRO":
                args.append("angle")
            measurement = self.read(*args)
            # put new reading to output queue
            if measurement:
                #if self.name == "GYRO":
                    #print("I'm alive!!!")
                self.queue.put(measurement)
                time.sleep(self.poll_period)

# main loop
if __name__ == "__main__":
    processors = {
            "GYRO": Vision("GYRO", 3),
            "LEFT": Driver("LEFT", "D"),
            "RIGHT": Driver("RIGHT", "A"),
            "GRABBER": Driver("GRABBER", "B"),
            "SWEEPER": Driver("SWEEPER", "C"),
            "COLOR": Vision("COLOR", 1)
            }
    brain = Megamind(processors)
    # EMERGENCY STOP (managed by main loop)
    stop = TouchSensor(2)
    try:
        import titlecard
        titlecard.show()
        print(f"{cpu_count()=}\n\n")
        #brain.queue.put_nowait(("GO", 50))
        #brain.queue.put_nowait(("TURN", 90))
        #brain.queue.put_nowait(("GO", 20))
        #brain.queue.put_nowait(("TURN", 90))

        #brain.queue.put_nowait(("GO", 20))
        #brain.queue.put_nowait(("GRAB", 10, 500))
        #brain.queue.put_nowait(("TURN", 15))
        #brain.queue.put_nowait(("GO", 10))
        #brain.queue.put_nowait(("GRAB", 12, 500))
        #brain.queue.put_nowait(("GO", 20, -320))
        #brain.queue.put_nowait(("GRAB", 10, -500))
        #brain.queue.put_nowait(("GO", 15, -320))
        #brain.queue.put_nowait(("GRAB", 10, -500))
        #brain.queue.put_nowait(("TURN", 720))
        #brain.queue.put_nowait(("GO_DOOR", 320))
        #brain.queue.put_nowait(("GRAB", 10, 500)) # for vibes
        #brain.queue.put_nowait(("GO", 15, 320))
        #brain.queue.put_nowait(("SWEEP", 190, True, 90))
        while True:
            turnDeg = input("Enter turn degrees")
            speed = input("Enter speed")
            brain.queue.put_nowait(("TURN", int(turnDeg), int(speed)))

        while not stop.is_pressed():
            sleep(0.01)
        raise Exception()
    except Exception as e:
        print(e)
    finally:
        print("killing...")
        brain.killAll()
        print("killed.")
        reset_brick()
