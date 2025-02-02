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
SEARCHING_FOR_LINE = 6
TURNING_TO_CROSS_FIELD = 7
LINING_TO_WALL = 8

# start out in the idle state
current_state = IDLE

turn_counter = 1

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
front_sonar_timer = Timer()

right_reflectance = Line(brain.three_wire_port.b)
left_reflectance = Line(brain.three_wire_port.a)

imu = Inertial(Ports.PORT6)

# calibrate imu
imu.calibrate()
# wait 2 seconds for imu to calibrate

imu.reset_rotation()

# 75" line to line
# 14" from the wall when turn to dead reckoning


def handleLeft1Button():
    global current_state

    if(current_state == IDLE):
        print('IDLE -> SEARCHING_FOR_LINE')
        current_state = SEARCHING_FOR_LINE

    else: # in any other state, the button acts as a kill switch
        print(' -> IDLE')
        current_state = IDLE
        left_motor.stop()
        right_motor.stop()


def encoderToInches(degrees):
  #  The motor has a 12-tooth gear, while the wheel has a 60-tooth gear. 
  # This means the motor spins 60/12 = 5 times faster than the wheel. 
  # The wheel has a diameter of 4 inches, so the circumference is 4*pi. 
  # Therefore, the motor must spin 5 * 4 * pi = 20*pi inches to make one full rotation.
  # The motor has a 360 degree rotation, so the number of degrees per inch is 360 / (20*pi) = 18/pi.
  # Therefore, the number of degrees per inch is 18/pi.
  return degrees * (3.14159/18)


def followLine(direction):
    # use right_reflectance and left_reflectance to follow the line
    # TRACING: 100 - 50 = 50, so robot is too far to the left
    # left motor gets 50 + 50*0.1 = 55
    # right motor gets 50 - 50*0.1 = 45
    # so robot should turn left
    error = right_reflectance.reflectivity() - left_reflectance.reflectivity()
    # print("error: " + str(error))
    base_speed_RPM = 200
    kP = 1
    if direction == "REVERSE":
      left_motor.spin(REVERSE, base_speed_RPM - error * kP, RPM)
      right_motor.spin(REVERSE, base_speed_RPM + error * kP, RPM)
    else:
      left_motor.spin(FORWARD, base_speed_RPM + error * kP, RPM)
      # print("left: " + str(base_speed_RPM + error * kP))
      right_motor.spin(FORWARD, base_speed_RPM - error * kP, RPM)
      # print("right: " + str(base_speed_RPM - error * kP))

def detectTurn():
   if right_reflectance.reflectivity() > 50 and left_reflectance.reflectivity() > 50:
      return True
   return False

def detectLine():
   if right_reflectance.reflectivity() < 50 and left_reflectance.reflectivity() > 50:
      return True
   return False

def turnByDegrees(direction, degrees, nextState):
    global current_state
    global turn_counter
    turn_counted = False
    imu.reset_rotation()
    print("imu rotation reset")

    while True:
      # print("target rotation: " + str(degrees))
      # print("actual rotation", imu.rotation())
      
      if(direction == "RIGHT"):
        left_motor.spin(FORWARD, 150, RPM)
        right_motor.stop()
      else:
        left_motor.stop()
        right_motor.spin(FORWARD, 150, RPM)

      if(abs(imu.rotation()) > abs(degrees)):
        break
    
    front_sonar_timer.clear()    
    # if(turn_counted == False):
    turn_counter += 1 # count the turns, so we know which one is turning to cross the field and needs to be more dictated by gyro
      # turn_counted = True
    current_state = nextState

def followHeading(direction):
  error = imu.rotation()
  # print("error: " + str(error))
  
  kP = 12.5
  base_speed_RPM = 200

  if direction == "REVERSE":
      left_motor.spin(REVERSE, base_speed_RPM - error * kP, RPM)
      right_motor.spin(REVERSE, base_speed_RPM + error * kP, RPM)
  else:
    left_motor.spin(FORWARD, base_speed_RPM - error * kP, RPM)
    # print("left: " + str(base_speed_RPM - error * kP))
    right_motor.spin(FORWARD, base_speed_RPM + error * kP, RPM)
    # print("right: " + str(base_speed_RPM + error * kP))

def goDistance(direction, distance, nextState):
    global current_state
    left_motor.reset_position()
    right_motor.reset_position()
    while True:
      # print("left motor: " + str(left_motor.position()))
      # print("left motor inches: " + str(encoderToInches(left_motor.position())))

      followHeading(direction)
      
      if(encoderToInches(left_motor.position()) > distance):
        break

    left_motor.stop()
    right_motor.stop()
    current_state = nextState

controller.buttonL1.pressed(handleLeft1Button)

while True:
    # if(checkMotionComplete()): handleMotionComplete()
    # print(reflectance.reflectivity())
    brain.screen.print("current state " + str(current_state))
    brain.screen.new_line()
    brain.screen.print("rotation " + str(imu.rotation()))
    brain.screen.new_line()
    brain.screen.print("turn count " + str(turn_counter))
    brain.screen.set_cursor(1, 1)
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
      left_motor.stop()
      right_motor.spin(FORWARD, 100, RPM)

      if(turn_counter == 3):
        turnByDegrees("LEFT", 90, LINING_TO_WALL)
      else:
        turnByDegrees("LEFT", 90, LINING)
      # current_state = LINING
      pass

    elif current_state == TURNING_RIGHT:
      if turn_counter == 4:
        current_state = TURNING_TO_CROSS_FIELD # override turn logic and turn 90 degrees to cross the field

      left_motor.spin(FORWARD, 100, RPM)
      right_motor.stop()

      if(turn_counter == 3):
        turnByDegrees("RIGHT", 90, LINING_TO_WALL)
      else:
        turnByDegrees("RIGHT", 90, LINING)
      # current_state = LINING
      pass

    elif current_state == LINING:
      followLine("FORWARD")
      if detectTurn():
        print(" -> TURNING")
        current_state = TURNING_RIGHT
      pass

    
    elif current_state == LINING_TO_WALL:
      followLine("FORWARD")

      print("distance: " + str(front_sonar.distance(INCHES)))
      print("time: " + str(front_sonar_timer.time()))


      if front_sonar.distance(INCHES) < 25 and front_sonar_timer.time() > 5000:
        print(" -> TURNING")
        current_state = TURNING_TO_CROSS_FIELD
      
    
    elif current_state == SEARCHING_FOR_LINE:
      # goDistance("FORWARD", 75, TURNING_LEFT)
      imu.reset_rotation() 
      print("imu rotation reset")
      
      while True:
        followHeading("FORWARD")
        if detectTurn():
          print("LINE FOUND!")
          print("SEARCHING_FOR_LINE -> TURNING")
          current_state = TURNING_RIGHT
          break

    elif current_state == TURNING_TO_CROSS_FIELD:
      turn_counter = 0
      turnByDegrees("RIGHT", 90, SEARCHING_FOR_LINE)

    else:
      print('Invalid state')
