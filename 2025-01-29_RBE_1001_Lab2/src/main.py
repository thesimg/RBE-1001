# ---------------------------------------------------------------------------- #
#                                                                              #
# 	Module:       main.py                                                      #
# 	Author:       thesimg                                                      #
# 	Created:      1/29/2025, 9:27:54 AM                                        #
# 	Description:  V5 project                                                   #
#                                                                              #
# ---------------------------------------------------------------------------- #
# Library imports
from vex import *

# define the states
IDLE = 0
DRIVING_FWD = 1
DRIVING_BKWD = 2
TURNING_LEFT = 3
TURNING_RIGHT = 4
LINING = 5

# start out in the idle state
current_state = IDLE

# Define the brain
brain=Brain()

# Motors
left_motor = Motor(Ports.PORT1, GearSetting.RATIO_18_1, True)
right_motor = Motor(Ports.PORT10, GearSetting.RATIO_18_1, False)
arm_motor = Motor(Ports.PORT8, GearSetting.RATIO_18_1, True);

# Controller
controller = Controller()

# Bumper
# bumper = Bumper(brain.three_wire_port.a)

# Sensor Declarations
front_sonar = Sonar(brain.three_wire_port.e)

right_reflectance = Line(brain.three_wire_port.b)
left_reflectance = Line(brain.three_wire_port.a)

imu = Inertial(Ports.PORT6)
initialHeading = imu.heading()
initialHeadingTimer = Timer()
initialHeadingTimeout = 7500

"""
Pro-tip: print out state _transistions_.
"""
def handleLeft1Button():
    global current_state

    if(current_state == IDLE):
        print('IDLE -> LINING')
        current_state = LINING

    else: # in any other state, the button acts as a kill switch
        print(' -> IDLE')
        current_state = IDLE
        left_motor.stop()
        right_motor.stop()


def followLine(direction):
    # use right_reflectance and left_reflectance to follow the line
    # TRACING: 100 - 50 = 50, so robot is too far to the left
    # left motor gets 50 + 50*0.1 = 55
    # right motor gets 50 - 50*0.1 = 45
    # so robot should turn left
    error = right_reflectance.reflectivity() - left_reflectance.reflectivity()
    print("error: " + str(error))
    base_speed_RPM = 100
    kP = 0.3
    if direction == "REVERSE":
      left_motor.spin(REVERSE, base_speed_RPM - error * kP, RPM)
      right_motor.spin(REVERSE, base_speed_RPM + error * kP, RPM)
    else:
      left_motor.spin(FORWARD, base_speed_RPM + error * kP, RPM)
      print("left: " + str(base_speed_RPM + error * kP))
      right_motor.spin(FORWARD, base_speed_RPM - error * kP, RPM)
      print("right: " + str(base_speed_RPM - error * kP))

def detectTurn():
   if right_reflectance.reflectivity() > 50 and left_reflectance.reflectivity() > 50:
      return True
   return False

def detectLine():
   if right_reflectance.reflectivity() < 50 and left_reflectance.reflectivity() > 50:
      return True
   return False


# TODO: make this more reusable, without using timer
def setInitialHeading():
    if(initialHeadingTimer.time() > initialHeadingTimeout):
        initialHeading = imu.heading()
        initialHeadingTimer.clear()
        brain.screen.print("resetting initial heading to: " + str(initialHeading))
        print("resetting initial heading to: " + str(initialHeading))
        return True
    else:
        return False



def turnByDegrees(direction, degrees):
    setInitialHeading()
    print("initial heading: " + str(initialHeading))
    print("target heading: " + str(degrees))
    print("actual heading", imu.heading())
    print("error", abs(imu.heading() - initialHeading))
    
    if(direction == "RIGHT"):
      left_motor.spin(FORWARD, 100, RPM)
      right_motor.stop()
    else:
      left_motor.stop()
      right_motor.spin(FORWARD, 100, RPM)
    
    if(abs(imu.heading() - initialHeading) > degrees):
      return True
    return False
   
      


controller.buttonL1.pressed(handleLeft1Button)

while True:
    # if(checkMotionComplete()): handleMotionComplete()
    # print(reflectance.reflectivity())
    # brain.screen.print(str(reflectance.reflectivity())+"\n")
    # brain.screen.set_cursor(1, 1)
    # print(front_sonar.distance(INCHES))
    # if(checkSonarComplete()): handleSonar()

    if current_state == IDLE:
      left_motor.stop()
      right_motor.stop()
      arm_motor.stop()

    elif current_state == DRIVING_FWD:
      pass

    elif current_state == DRIVING_BKWD:
      pass

    elif current_state == TURNING_LEFT:
      pass

    elif current_state == TURNING_RIGHT:
      left_motor.spin(FORWARD, 100, RPM)
      right_motor.stop()

      if(turnByDegrees("RIGHT", 70)):
         current_state = LINING

      pass

    elif current_state == LINING:
      followLine("FORWARD")
      if detectTurn():
        print(" -> TURNING")
        current_state = TURNING_RIGHT
         
      pass

    else:
      print('Invalid state')


## TODO: Add various checkers/handlers; print ultrasonice; etc. See handout.