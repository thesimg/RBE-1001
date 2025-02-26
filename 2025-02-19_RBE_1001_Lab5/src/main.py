# ---------------------------------------------------------------------------- #
#                                                                              #
# 	Module:       main.py                                                      #
# 	Author:       thesimg                                                      #
# 	Created:      2/19/2025, 8:10:34 AM                                        #
# 	Description:  V5 project                                                   #
#                                                                              #
# ---------------------------------------------------------------------------- #


# Library imports
from vex import *

# Brain should be defined by default
brain = Brain()

controller = Controller()

## Define states and state variable
IDLE = 0
SEARCHING_FOR_FRUIT = 1
DRIVING_TO_FRUIT = 2
HARVESTING_FRUIT = 3
LINING_BY_DISTANCE = 4
LINING_BY_LINE = 5
TURNING_TO_HEADING = 6
TURNING_TO_FRUIT = 7
TURNING_TO_BASKETS = 8
SQUARING_TO_WALL = 9
LINING_BY_ULTRASONIC = 10
LINING_BY_DISTANCE_SHORT = 11
TURNING_TO_FRUIT_2 = 12

current_state = IDLE

total_harvests = 0



# Define the motors
left_motor = Motor(Ports.PORT1, GearSetting.RATIO_18_1, True)
left_motor.reset_position()
right_motor = Motor(Ports.PORT10, GearSetting.RATIO_18_1, False)
right_motor.reset_position()

lift_motor = Motor(Ports.PORT3, GearSetting.RATIO_18_1, False)

hopper_motor = Motor(Ports.PORT8, GearSetting.RATIO_18_1, False)
hopper_motor.set_position(0, DEGREES)
hopper_motor.spin_to_position(75)

## Define the camera (vision)
## Note that we define the signatures first and then pass them to the Vision constructor --
## I don't know if that is truly needed or not
Vision__LIME = Signature (1, -6069, -4855, -5462, -3131, -2407, -2769, 3.900, 0)
Vision__LEMON = Signature (2, 131, 425, 278, -3915, -3429, -3672, 7.400, 0)
Vision__ORANGUTAN = Signature (3, 5323, 6263, 5793, -2717, -2111, -2414, 1.900, 0)
# Vision__DRAGONFRUIT = Signature (4, 5231, 5733, 5482, 2935, 3963, 3449, 10, 0)

camera = Vision (Ports.PORT7, 50, Vision__LEMON, Vision__LIME, Vision__ORANGUTAN)

# Sensor Declarations
front_sonar = Sonar(brain.three_wire_port.e)
front_sonar_timer = Timer()

right_front_reflectance = Line(brain.three_wire_port.b)
left_front_reflectance = Line(brain.three_wire_port.a)

right_back_reflectance = Line(brain.three_wire_port.c)
left_back_reflectance = Line(brain.three_wire_port.d)

imu = Inertial(Ports.PORT6)

# calibrate imu
imu.calibrate()
# wait 2 seconds for imu to calibrate

imu.reset_rotation()

# utilities
def setState(newState):
    global current_state
    if(not imu.is_calibrating()):
      print("State changed from " + str(current_state) + " to " + str(newState))
      current_state = newState
    else:
      print("imu is calibrating, not changing state")

lemonViews = 0
dragonfruitViews = 0
bothViews = 0
overallTrials = 0

def checkForFruit():
    seesLemon = False
    seesDragonfruit = False
    global lemonViews
    global dragonfruitViews
    global bothViews
    global overallTrials

    lemons = camera.take_snapshot(Vision__LEMON)
    # limes = camera.take_snapshot(Vision__LIME)
    # orangutans = camera.take_snapshot(Vision__ORANGUTAN)
    # dragonfruits = camera.take_snapshot(Vision__DRAGONFRUIT)

    # print("largest object x:", camera.largest_object().centerX, "  y: ", camera.largest_object().centerY, "  w: ", camera.largest_object().width, "  h: ", camera.largest_object().height)

    if(lemons and camera.largest_object().width > 30):
        # print("count: " + str(camera.object_count))
        # print("largest object x:", camera.largest_object().centerX, "  y: ", camera.largest_object().centerY, "  w: ", camera.largest_object().width, "  h: ", camera.largest_object().height)
        # print("Dragonfruit detected")
        seesDragonfruit = True
    
    lemons = camera.take_snapshot(Vision__LEMON)

    if(lemons and camera.largest_object().width > 30):
        # print("count: " + str(camera.object_count))
        # print("largest object x:", camera.largest_object().centerX, "  y: ", camera.largest_object().centerY, "  w: ", camera.largest_object().width, "  h: ", camera.largest_object().height)
        # print("Lemon detected")
        seesLemon = True

    if(seesLemon and seesDragonfruit):
        bothViews += 1
        print("Both fruits detected, " + str(bothViews) + " times")
    elif(seesLemon):
        lemonViews += 1
        print("Only Lemon detected, " + str(lemonViews) + " times")
    elif(seesDragonfruit):
        dragonfruitViews += 1
        print("Only Dragonfruit detected, " + str(dragonfruitViews) + " times")
    overallTrials += 1
    print("Overall trials: " + str(overallTrials))


controller.buttonL1.pressed(lambda: setState(LINING_BY_DISTANCE))


lastTwentyFruitY = [0] * 20
def driveToFruit(type):
    snapshot = camera.take_snapshot(Vision__LEMON)
    if type == "lemon":
      # lemons = camera.take_snapshot(Vision__LEMON)
    # elif type == "dragonfruit":
    #   dragonfruits = camera.take_snapshot(Vision__DRAGONFRUIT)
      snapshot = camera.take_snapshot(Vision__LEMON)
    elif type == "lime":
      # limes = camera.take_snapshot(Vision__LIME)
      snapshot = camera.take_snapshot(Vision__LIME)
    elif type == "orangutan":
      # orangutans = camera.take_snapshot(Vision__ORANGUTAN)
      snapshot = camera.take_snapshot(Vision__ORANGUTAN)
    else:
      # lemons = camera.take_snapshot(Vision__LEMON)
      snapshot = camera.take_snapshot(Vision__LEMON)


    if(snapshot):
      print("largerst object w: ", camera.largest_object().width, "  h: ", camera.largest_object().height)
      if(camera.largest_object().width > 40 and camera.largest_object().height > 40):
        object_x = camera.largest_object().centerX
        object_y = camera.largest_object().centerY
        object_height = camera.largest_object().height

        left_power = 0
        right_power = 0

        # TURN
        kP_turn = -1.5 #0.75 # 3
        x_error = object_x - 157.5
        left_turn_power = kP_turn * x_error
        right_turn_power = kP_turn * -x_error
        # left_motor.spin(REVERSE, 10 + kP_turn * x_error)
        # right_motor.spin(REVERSE, 10 - kP_turn * x_error)
        
        # DRIVE
        kP_drive = 2 # 2.5
        drive_error = object_height - 150
        left_drive_power = kP_drive * drive_error
        right_drive_power = kP_drive * drive_error

        left_power = left_drive_power - left_turn_power
        right_power = right_drive_power - right_turn_power

        print("\n\n\n")
        print("height: " + str(object_height))
        print("left turn power: " + str(left_turn_power) + "  right turn power: " + str(right_turn_power))
        print("left drive power: " + str(left_drive_power) + "  right drive power: " + str(right_drive_power))
        print("left power: " + str(left_power) + "  right power: " + str(right_power))
        print("\n")

        left_motor.spin(REVERSE, left_power, PERCENT)
        right_motor.spin(REVERSE, right_power, PERCENT)

        # LIFT
        # update the last twenty fruit y values
        lastTwentyFruitY.pop(0)
        lastTwentyFruitY.append(object_y)

        # get average of last twenty fruit y values to smooth out the values (TODO: replace with better filter)
        avgFruitY = sum(lastTwentyFruitY) / len(lastTwentyFruitY)

        kP_lift = 4.5 # 4.5
        y_error = avgFruitY - 140 #105.5
        lift_power = kP_lift * y_error
        lift_motor.spin(FORWARD, lift_power, PERCENT)

        print("object y: " + str(object_y))
        print("lift (y) error: " + str(y_error))
        print("lift power: " + str(lift_power))

        if(object_height > 120 and abs(x_error) < 5 and abs(x_error) < 5):
            print("Object is close enough")
            return True
      else:
        print("Object is too far away")
        # left_motor.stop()
        # right_motor.stop()
        left_motor.spin(FORWARD, 50, RPM)
        right_motor.spin(REVERSE, 50, RPM)
        lift_motor.stop()


def calcDistanceFromPixels(width_px):
    # print out the distance from the object in cm, using pinhole approximation, using width of the block in pixels
    # the block is 20cm wide, subtends 30 px at 50cm, subtends 15px at 100cm
    # the relationship derived earlier is s1px1 = s2px2, this px2 = s1px1/s2
    # if s1 = 50cm, px1 = 30, px2 = width_px
    # s2 = 50 * 30 / width_px
    if(width_px <= 0):
        return "error: width must be greater than 0"
    return (50 * 30) / width_px


def encoderToInches(degrees):
  # The motor has a 12-tooth gear, while the wheel has a 60-tooth gear. 
  # This means the motor spins 60/12 = 5 times faster than the wheel. 
  # The wheel has a diameter of 4 inches, so the circumference is 4*pi. 
  # Therefore, the motor must spin 5 * 4 * pi = 20*pi inches to make one full rotation.
  # The motor has a 360 degree rotation, so the number of degrees per inch is 360 / (20*pi) = 18/pi.
  # Therefore, the number of degrees per inch is 18/pi.
  return degrees / (130.24367)


def followLine(direction, side):
    # use right_front_reflectance and left_front_reflectance to follow the line
    # TRACING: 100 - 50 = 50, so robot is too far to the left
    # left motor gets 50 + 50*0.1 = 55
    # right motor gets 50 - 50*0.1 = 45
    # so robot should turn left
    front_error = right_front_reflectance.reflectivity() - left_front_reflectance.reflectivity()
    rear_error = right_back_reflectance.reflectivity() - left_back_reflectance.reflectivity()
    # print("error: " + str(error))
    base_speed_RPM = 100 # 100
    kP = 1 # 1
    if side == "FRONT":
      if direction == "REVERSE":
          left_motor.spin(REVERSE, base_speed_RPM + front_error * kP, RPM)
          right_motor.spin(REVERSE, base_speed_RPM - front_error * kP, RPM)
      else:
        left_motor.spin(FORWARD, base_speed_RPM - front_error * kP, RPM)
        # print("left: " + str(base_speed_RPM - error * kP))
        right_motor.spin(FORWARD, base_speed_RPM + front_error * kP, RPM)
        # print("right: " + str(base_speed_RPM + error * kP))
    else:
      print("rear error: " + str(rear_error))
      print("rear left: " + str(left_back_reflectance.reflectivity()))
      print("rear right: " + str(right_back_reflectance.reflectivity()))
      if direction == "REVERSE":
        left_motor.spin(REVERSE, base_speed_RPM + rear_error * kP, RPM)
        right_motor.spin(REVERSE, base_speed_RPM - rear_error * kP, RPM)
      else:
        left_motor.spin(FORWARD, base_speed_RPM + rear_error * kP, RPM)
        # print("left: " + str(base_speed_RPM - error * kP))
        right_motor.spin(FORWARD, base_speed_RPM - rear_error * kP, RPM)
        # print("right: " + str(base_speed_RPM + error * kP))


def detectBothReflecting(): # i.e. detect the line
   if right_front_reflectance.reflectivity() > 50 and left_front_reflectance.reflectivity() > 50:
      return True
   return False

def detectLeftReflecting():
   if right_front_reflectance.reflectivity() < 50 and left_front_reflectance.reflectivity() > 50:
      return True
   return False

def turnByDegrees(direction, degrees, nextState):
    global current_state
    # imu.reset_rotation()
    # print("imu rotation reset")

    while True:
      print("target rotation: " + str(degrees))
      print("actual rotation", imu.rotation())
      print("tolerance: " + str(abs(abs(degrees))-abs(imu.rotation())))
      
      if(abs(abs(degrees)-abs(imu.rotation())) < 0.5):
        print("turn complete")
        left_motor.stop()
        right_motor.stop()
        print("motors stopped")
        break
      else:
        print("actual rotation", imu.rotation())
        # if turn is right, rotation is positive
        # turn to 90, start at 0, so error is 90 - 0 = 90
        # so left motor goes forward, right motor goes reverse 
        error = degrees - imu.rotation()
        kP = 4
        left_motor.spin(FORWARD, 5+error * kP, RPM)
        right_motor.spin(FORWARD, 5-error * kP, RPM)


        # if(direction == "RIGHT"):
        #   left_motor.spin(FORWARD, 150, RPM)
        #   right_motor.spin(REVERSE, 150, RPM)
        #   # right_motor.stop()
        # else:
        #   # left_motor.stop()
        #   left_motor.spin(REVERSE, 150, RPM)
        #   right_motor.spin(FORWARD, 150, RPM)
    # front_sonar_timer.clear()    
    print("state changing from " + str(current_state) + " to " + str(nextState))
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
      print("left motor: " + str(left_motor.position()))
      print("left motor inches: " + str(encoderToInches(left_motor.position())))

      followHeading(direction)
      
      if(encoderToInches(left_motor.position()) > distance):
        break

    left_motor.stop()
    right_motor.stop()
    current_state = nextState

def trackDistanceTraveled(distance):
  while (True):
    print("left motor: " + str(left_motor.position(TURNS)))
    print("left motor inches: " + str(encoderToInches(left_motor.position(TURNS))))
    if(encoderToInches(abs(left_motor.position(DEGREES))) > distance): 
      return True
    else:
      return False

## Our main loop
while True:
    ## if enough cycles have passed without a detection, we've lost the object
    # if(checkForLostObject()): handleLostObject()
    # print("current state: " + str(current_state))

    if(controller.buttonL2.pressing() and current_state != IDLE):
        print("emergency stop")
        setState(IDLE)
    
    brain.screen.print("current state " + str(current_state))
    brain.screen.new_line()
    brain.screen.print("rotation " + str(imu.rotation()))
    brain.screen.new_line()
    brain.screen.print("total harvests " + str(total_harvests))
    brain.screen.new_line()
    brain.screen.set_cursor(1, 1)

    if current_state == IDLE:
      left_motor.stop()
      right_motor.stop()
      lift_motor.stop()
      # hopper_motor.stop()
      
    elif current_state == LINING_BY_DISTANCE:
      print("starting lining by distance")
      while(not trackDistanceTraveled(20)):
        followLine("FORWARD", "FRONT")
        print("degrees: " + str(left_motor.position(DEGREES)))
        print("distance traveled: " + str(encoderToInches(left_motor.position(DEGREES))))
      setState(TURNING_TO_FRUIT)

    elif current_state == TURNING_TO_FRUIT:
        turnByDegrees("RIGHT", 90, DRIVING_TO_FRUIT)
    
    elif current_state == LINING_BY_LINE:
       pass
    
    elif current_state == SEARCHING_FOR_FRUIT:
        pass

    elif current_state == DRIVING_TO_FRUIT:
        if driveToFruit("lemon"): # once the object is close enough, start harvesting
            setState(HARVESTING_FRUIT)

    elif current_state == HARVESTING_FRUIT:
        # lower the lift, this is kinda placeholder code until we get the actual lift mechanism & logic working
        left_motor.stop()
        right_motor.stop()
        lift_motor.stop()

        right_motor.spin(FORWARD, 100, RPM)
        left_motor.spin_for(FORWARD, 2.75, TURNS, 100, RPM)
        # right_motor.spin_for(FORWARD, 10, TURNS, 50, RPM)
        right_motor.stop()

        print("driven to fruit, harvesting next")
        
        lift_motor.spin_for(REVERSE, 1.5, TURNS, 50, RPM)

        
        right_motor.spin(REVERSE, 200, RPM)
        lift_motor.spin(FORWARD, 100, RPM)
        left_motor.spin_for(REVERSE, 5, TURNS, 200, RPM)
        right_motor.stop()

        total_harvests += 1

        if(total_harvests == 1):
          setState(TURNING_TO_FRUIT_2)
        if(total_harvests == 2):
          setState(TURNING_TO_BASKETS)
          
    elif current_state == TURNING_TO_BASKETS:
      left_motor.spin(REVERSE, 100, RPM)
      right_motor.spin_for(REVERSE, 2, TURNS, 100, RPM)
      left_motor.stop()
      turnByDegrees("LEFT", 180, LINING_BY_ULTRASONIC)

    elif current_state == TURNING_TO_FRUIT_2:
      left_motor.spin(REVERSE, 100, RPM)
      right_motor.spin_for(REVERSE, 2, TURNS, 100, RPM)
      left_motor.stop()
      turnByDegrees("LEFT", 0, LINING_BY_DISTANCE_SHORT)
        
    elif current_state == LINING_BY_ULTRASONIC:
      front_sonar_timer.clear()
      while True:
        if(front_sonar.distance(INCHES) < 2):
          left_motor.stop()
          right_motor.stop()
          hopper_motor.spin_to_position(10)
          setState(IDLE)
        else:
           followLine("FORWARD", "FRONT")
          # followHeading("FORWARD")

    elif current_state == LINING_BY_DISTANCE_SHORT:  
      print("starting lining by distance")
      while(not trackDistanceTraveled(5)):
        followLine("FORWARD", "FRONT")
        print("degrees: " + str(left_motor.position(DEGREES)))
        print("distance traveled: " + str(encoderToInches(left_motor.position(DEGREES))))
      setState(TURNING_TO_FRUIT)

    elif current_state == TURNING_TO_FRUIT_2:
        turnByDegrees("RIGHT", 90, DRIVING_TO_FRUIT)

