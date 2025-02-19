# ---------------------------------------------------------------------------- #
#                                                                              #
# 	Module:       main.py                                                      #
# 	Author:       thesimg                                                      #
# 	Created:      2/2/2025, 2:51:26 AM                                         #
# 	Description:  V5 project                                                   #
#                                                                              #
# ---------------------------------------------------------------------------- #

# Library imports
from vex import *

# Brain should be defined by default
brain=Brain()

brain.screen.print("Hello V5")

left_motor = Motor(Ports.PORT1)
right_motor = Motor(Ports.PORT2)
imu = Inertial(Ports.PORT3)


def controlHeading(targetHeading, forwardSpeed):
    kP = 1.0

    while True:
        # uses modulus to wrap imu between -180 and 180
        error = ((targetHeading - imu.heading() + 180) % 360) - 180

        # forwardSpeed * 5 because the drive motors are geared down 5:1
        # effort is kP * error, added or subtracted from each side of the drive
        left_motor.spin(FORWARD, (forwardSpeed*5) - kP*error, RPM)
        right_motor.spin(FORWARD, (forwardSpeed*5) + kP*error, RPM)