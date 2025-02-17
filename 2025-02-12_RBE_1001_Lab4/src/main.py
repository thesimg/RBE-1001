# ---------------------------------------------------------------------------- #
#                                                                              #
# 	Module:       main.py                                                      #
# 	Author:       thesimg                                                      #
# 	Created:      2/12/2025, 9:16:57 AM                                        #
# 	Description:  V5 project                                                   #
#                                                                              #
# ---------------------------------------------------------------------------- #
'''
This code demonstrates a basic search and drive towards behaviour with the camera.

The robot has three states:
    IDLE - waiting for the button press
    SEARCHING - spins slowly until it finds an object
    APPROACHING - drives towards the object

Camera checking is done on a timer. If no object is found, a counter is incremented and
if the counter reaches a threshold, the robot goes back into searching mode.
'''

# Library imports
from vex import *

# Brain should be defined by default
brain = Brain()

controller = Controller()

imu = Inertial(Ports.PORT6)

# calibrate imu
imu.calibrate()
# wait 2 seconds for imu to calibrate

imu.reset_rotation()


## Define states and state variable
IDLE = 0
SEARCHING_FOR_FRUIT = 1
DRIVING_TO_FRUIT = 2
HARVESTING_FRUIT = 3

current_state = IDLE

# Define the motors
left_motor = Motor(Ports.PORT1, GearSetting.RATIO_18_1, False)
right_motor = Motor(Ports.PORT10, GearSetting.RATIO_18_1, True)

lift_motor = Motor(Ports.PORT8, GearSetting.RATIO_18_1, False)


## Define the camera (vision)
## Note that we define the signatures first and then pass them to the Vision constructor --
## I don't know if that is truly needed or not
Vision__LIME = Signature (1, -6069, -4855, -5462, -3131, -2407, -2769, 3.9, 0)
Vision__LEMON = Signature (2, 2967, 3781, 3374, -3731, -3459, -3595, 9.1, 0)
Vision__ORANGUTAN = Signature (3, 7895, 8839, 8367, -2645, -2313, -2479, 6.9, 0)
Vision__DRAGONFRUIT = Signature (4, 5231, 5733, 5482, 2935, 3963, 3449, 10, 0)

camera = Vision (Ports.PORT7, 50, Vision__LEMON, Vision__DRAGONFRUIT)

# utilities
def setState(newState):
    global current_state
    current_state = newState

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

    # lemons = camera.take_snapshot(Vision__LEMON)
    # limes = camera.take_snapshot(Vision__LIME)
    # orangutans = camera.take_snapshot(Vision__ORANGUTAN)
    dragonfruits = camera.take_snapshot(Vision__DRAGONFRUIT)

    # print("largest object x:", camera.largest_object().centerX, "  y: ", camera.largest_object().centerY, "  w: ", camera.largest_object().width, "  h: ", camera.largest_object().height)

    if(dragonfruits and camera.largest_object().width > 30):
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

def buttonPressed():
    print("button pressed")

# controller.buttonL1.pressed(checkForFruit)
# controller.buttonL1.pressed(buttonPressed)
controller.buttonL2.pressed(lambda: setState(DRIVING_TO_FRUIT))

def driveToFruit():
    lemons = camera.take_snapshot(Vision__LEMON)

    if(lemons):
        object_x = camera.largest_object().centerX
        object_y = camera.largest_object().centerY
        object_height = camera.largest_object().height

        left_power = 0
        right_power = 0

        # DRIVE
        # target_x = 160
        # TURN
        kP_turn = 0.01
        x_error = object_x - 157.5
        left_turn_power = kP_turn * x_error
        right_turn_power = -kP_turn * x_error
        # left_motor.spin(REVERSE, 10 + kP_turn * x_error)
        # right_motor.spin(REVERSE, 10 - kP_turn * x_error)
        
        # DRIVE
        kP_drive = 0.01
        drive_error = object_height - 200
        left_drive_power = kP_drive * drive_error
        right_drive_power = kP_drive * drive_error

        left_power = left_drive_power - left_turn_power
        right_power = right_drive_power - right_turn_power

        print("left turn power: " + str(left_turn_power) + "  right turn power: " + str(right_turn_power))
        print("left drive power: " + str(left_drive_power) + "  right drive power: " + str(right_drive_power))
        print("left power: " + str(left_power) + "  right power: " + str(right_power))
        print("\n")

        left_motor.spin(FORWARD, left_power)
        right_motor.spin(FORWARD, right_power)

        # LIFT
        kP_lift = 0.01
        y_error = object_y - 105.5
        lift_power = kP_lift * y_error
        lift_motor.spin(FORWARD, lift_power)

        print("lift (y) error: " + str(y_error))
        print("lift power: " + str(lift_power))
        print("\n\n")

        if(object_height > 200):
            print("Object is close enough")
            return True


def calcDistanceFromPixels(width_px):
    # print out the distance from the object in cm, using pinhole approximation, using width of the block in pixels
    # the block is 20cm wide, subtends 30 px at 50cm, subtends 15px at 100cm
    # the relationship derived earlier is s1px1 = s2px2, this px2 = s1px1/s2
    # if s1 = 50cm, px1 = 30, px2 = width_px
    # s2 = 50 * 30 / width_px
    if(width_px <= 0):
        return "error: width must be greater than 0"
    return (50 * 30) / width_px



## Our main loop
while True:
    ## if enough cycles have passed without a detection, we've lost the object
    # if(checkForLostObject()): handleLostObject()
    
    brain.screen.print("current state " + str(current_state))
    brain.screen.new_line()
    brain.screen.print("rotation " + str(imu.rotation()))
    brain.screen.new_line()
    brain.screen.set_cursor(1, 1)

    if current_state == IDLE:
        pass
    elif current_state == SEARCHING_FOR_FRUIT:
        pass
    elif current_state == DRIVING_TO_FRUIT:
        if driveToFruit(): # once the object is close enough, start harvesting
            setState(HARVESTING_FRUIT)
    elif current_state == HARVESTING_FRUIT:
        # lower the lift, this is kinda placeholder code until we get the actual lift mechanism & logic working
        lift_motor.spin_for(FORWARD, 1000, DEGREES, 50, RPM)
        setState(IDLE)
        





# def turnByDegrees(direction, degrees, nextState):
#     # global current_state
#     # global turn_counter
#     turn_counted = False
#     imu.reset_rotation()
#     print("imu rotation reset")

#     while True:
#       # print("target rotation: " + str(degrees))
#       # print("actual rotation", imu.rotation())
      
#       if(direction == "RIGHT"):
#         left_motor.spin(FORWARD, 150, RPM)
#         right_motor.stop()
#       else:
#         left_motor.stop()
#         right_motor.spin(FORWARD, 150, RPM)

#       if(abs(imu.rotation()) > abs(degrees)):
#         break
    
#     # front_sonar_timer.clear()    
#     # # if(turn_counted == False):
#     # turn_counter += 1 # count the turns, so we know which one is turning to cross the field and needs to be more dictated by gyro
#     #   # turn_counted = True
#     # current_state = nextState


'''
The button (bumper) makes use of the built-in event system.
'''
# button = Bumper(brain.three_wire_port.g)

# def handleButton():
#     global current_state

#     if(current_state == ROBOT_IDLE):
#         print('IDLE -> SEARCHING') ## Pro-tip: print out state _transitions_
#         current_state = ROBOT_SEARCHING
#         # left_motor.spin(FORWARD, 30)
#         # right_motor.spin(FORWARD, -30)

#         ## start the timer for the camera
#         cameraTimer.event(cameraTimerCallback, 50)

#     else: ## failsafe; go to IDLE from any other state when button is pressed
#         print(' -> IDLE')
#         current_state = ROBOT_IDLE
#         left_motor.stop()
#         right_motor.stop()


'''
We'll keep track of missed detections. If it exceeds some threshold, go back to SEARCHING
'''
# missedDetections = 0
# def handleLostObject():
#     global current_state
#     if current_state == ROBOT_APPROACHING:
#         print('APPROACHING -> SEARCHING') ## Pro-tip: print out state _transitions_
#         current_state = ROBOT_SEARCHING
#         left_motor.spin(FORWARD, 30)
#         right_motor.spin(FORWARD, -30)

'''
We'll use a timer to read the camera every cameraInterval milliseconds
'''
# cameraInterval = 50
# cameraTimer = Timer()

# def cameraTimerCallback():
#     global current_state
#     global missedDetections

#     ## Here we use a checker-handler, where the checker checks if there is a new object detection.
#     ## We don't use a "CheckForObjects()" function because take_snapshot() acts as the checker.
#     ## It returns a non-empty list if there is a detection.
#     objects = camera.take_snapshot(Vision__LEMON)
#     if objects: handleObjectDetection()
#     else: missedDetections = missedDetections + 1

#     # restart the timer
#     if(current_state != ROBOT_IDLE):
#         cameraTimer.event(cameraTimerCallback, 50)


# def handleObjectDetection():
#     global current_state
#     global object_timer
#     global missedDetections

#     cx = camera.largest_object().centerX
#     cy = camera.largest_object().centerY

#     ## TODO: Add code to print out the coordinates and size


#     if current_state == ROBOT_SEARCHING:
#         print('SEARCHING -> APPROACHING') ## Pro-tip: print out state _transitions_
#         current_state = ROBOT_APPROACHING

#     ## Not elif, because we want the logic to cascade
#     if current_state == ROBOT_APPROACHING:

#         target_x = 160
#         K_x = 0.5

#         error = cx - target_x
#         turn_effort = K_x * error


#         ## TODO: Edit code to approach or back up to hold the right position
#         left_motor.spin(REVERSE, 10 + turn_effort)
#         right_motor.spin(REVERSE, 10 - turn_effort)

#     ## reset the time out timer
#     missedDetections = 0

# def checkForLostObject():
#     ## this is not a "proper" event checker -- need to be reasonable
#     if(missedDetections > 20): return True
#     else: return False
