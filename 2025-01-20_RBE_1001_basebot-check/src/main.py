# ---------------------------------------------------------------------------- #
#                                                                              #
# 	Module:       main.py                                                      #
# 	Author:       thesimg                                                      #
# 	Created:      1/20/2025, 5:45:12 PM                                        #
# 	Description:  V5 project                                                   #
#                                                                              #
# ---------------------------------------------------------------------------- #

# Library imports
from vex import *

# Brain should be defined by default
brain=Brain()

brain.screen.print("Hello, World!")


# Goal: rotate at 30rpm for one rotation, then stop
left_motor = Motor(Ports.PORT10, True)
right_motor = Motor(Ports.PORT1)

# 12 tooth gear on motor, 60 tooth gear on wheel
# goal: wheel spinning at 30rpm
# 30rpm * 60/12 = 150rpm

run = True
while(run):
  left_motor.spin(FORWARD, 150, RPM)
  right_motor.spin(FORWARD, 150, RPM)
  wait(2000)
  left_motor.stop()
  right_motor.stop()
  run = False
