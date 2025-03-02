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

current_step = 10000

# Define the motors
left_motor = Motor(Ports.PORT1, GearSetting.RATIO_18_1, True)
left_motor.reset_position()
right_motor = Motor(Ports.PORT10, GearSetting.RATIO_18_1, False)
right_motor.reset_position()

lift_motor = Motor(Ports.PORT3, GearSetting.RATIO_18_1, False)

hopper_motor = Motor(Ports.PORT8, GearSetting.RATIO_18_1, False)
hopper_motor.set_position(0, DEGREES)
hopper_motor.spin_to_position(75)

left_back_bumper = Bumper(brain.three_wire_port.h)
right_back_bumper = Bumper(brain.three_wire_port.g)

## Define the camera (vision)
## Note that we define the signatures first and then pass them to the Vision constructor --
## I don't know if that is truly needed or not
Vision__LIME = Signature (1, -6069, -4855, -5462, -3131, -2407, -2769, 3.900, 0)
Vision__LEMON = Signature (2, 131, 425, 278, -3915, -3429, -3672, 7.400, 0)
Vision__ORANGUTAN = Signature (3, 5323, 6263, 5793, -2717, -2111, -2414, 5.9, 0)
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

def restartProgram():
    right_motor.stop()
    left_motor.stop()
    lift_motor.stop()
    current_step = 0

controller.buttonL1.pressed(lambda: restartProgram())

lastTwentyFruitY = [0] * 20

def driveToFruit(type):
    """
    Uses the vision sensor to locate a fruit of the given type and drives toward it.
    Adjusts both steering and forward movement based on vision input.
    """
    # Select the correct vision snapshot
    if type == "lemon":
        snapshot = camera.take_snapshot(Vision__LEMON)
    elif type == "lime":
        snapshot = camera.take_snapshot(Vision__LIME)
    elif type == "orangutan":
        snapshot = camera.take_snapshot(Vision__ORANGUTAN)
    else:
        snapshot = camera.take_snapshot(Vision__LEMON)

    if snapshot:
        print("Largest object - Width:", camera.largest_object().width, "Height:", camera.largest_object().height)
        if camera.largest_object().width > 40 and camera.largest_object().height > 40:
            object_x = camera.largest_object().centerX
            object_y = camera.largest_object().centerY
            object_height = camera.largest_object().height

            # Adjust turn based on object's X position
            kP_turn = -1.5
            x_error = object_x - 157.5
            left_turn_power = kP_turn * x_error
            right_turn_power = kP_turn * -x_error
            
            # Adjust drive speed based on object's height
            kP_drive = 2
            drive_error = object_height - 150
            left_drive_power = kP_drive * drive_error
            right_drive_power = kP_drive * drive_error

            left_power = left_drive_power - left_turn_power
            right_power = right_drive_power - right_turn_power

            print("Height: " + str(object_height) + "Left Power: " + str(left_power) + "Right Power: " + str(right_power))

            left_motor.spin(REVERSE, left_power, PERCENT)
            right_motor.spin(REVERSE, right_power, PERCENT)

            # Adjust lift height based on Y position
            lastTwentyFruitY.pop(0)
            lastTwentyFruitY.append(object_y)
            avgFruitY = sum(lastTwentyFruitY) / len(lastTwentyFruitY)

            kP_lift = 4.5
            y_error = avgFruitY - 140
            lift_power = kP_lift * y_error
            lift_motor.spin(FORWARD, lift_power, PERCENT)

            print("Object Y: " + str(object_y) + "Lift Power: " + str(lift_power))

            # Stop when the object is close enough and centered
            if object_height > 120 and abs(x_error) < 5:
                print("Object is close enough")
                return True
        else:
            print("Object is too far away, adjusting position")
            # left_motor.spin(FORWARD, 50, RPM)
            # right_motor.spin(REVERSE, 50, RPM)
            # lift_motor.stop()
    return False

def encoderToInches(degrees):
    """
    Converts motor encoder degrees to inches traveled based on gear ratio.
    """
    return degrees / 130.24367

def followLine(direction, side):
    """
    Uses the reflectance sensors to follow a line, adjusting motor speeds accordingly.
    """
    front_error = right_front_reflectance.reflectivity() - left_front_reflectance.reflectivity()
    rear_error = right_back_reflectance.reflectivity() - left_back_reflectance.reflectivity()
    
    base_speed_RPM = 25
    front_kP = 0.5
    back_kP = 0.02

    left_motor_power = (base_speed_RPM - front_error * front_kP) + (base_speed_RPM - rear_error * back_kP)
    right_motor_power = (base_speed_RPM + front_error * front_kP) + (base_speed_RPM + rear_error * back_kP)

    # if side == "FRONT":
    #     if direction == "REVERSE":
    #         left_motor.spin(REVERSE, base_speed_RPM + front_error * kP, RPM)
    #         right_motor.spin(REVERSE, base_speed_RPM - front_error * kP, RPM)
    #     else:
    #         left_motor.spin(FORWARD, base_speed_RPM - front_error * kP, RPM)
    #         right_motor.spin(FORWARD, base_speed_RPM + front_error * kP, RPM)
    # else:
    #     if direction == "REVERSE":
    #         left_motor.spin(REVERSE, base_speed_RPM + rear_error * kP, RPM)
    #         right_motor.spin(REVERSE, base_speed_RPM - rear_error * kP, RPM)
    #     else:
    #         left_motor.spin(FORWARD, base_speed_RPM + rear_error * kP, RPM)
    #         right_motor.spin(FORWARD, base_speed_RPM - rear_error * kP, RPM)
    
    left_motor.spin(FORWARD, left_motor_power, RPM)
    right_motor.spin(FORWARD, right_motor_power, RPM)

def detectBothReflecting():
    """
    Returns True if both front reflectance sensors detect the line.
    """
    return right_front_reflectance.reflectivity() > 50 and left_front_reflectance.reflectivity() > 50

def detectLeftReflecting():
    """
    Returns True if only the left front reflectance sensor detects the line.
    """
    return right_front_reflectance.reflectivity() < 50 and left_front_reflectance.reflectivity() > 50

def turnByDegrees(degrees):
    """
    Uses the IMU to turn the robot by a specified number of degrees.
    """
    # imu.reset_rotation()
    # print("IMU rotation reset")

    while True:
        print("Target Rotation: " + str(degrees) + "Actual Rotation: " + str(imu.rotation()))
        
        if abs(degrees - imu.rotation()) < 0.5:
            print("Turn complete")
            left_motor.stop()
            right_motor.stop()
            return True

        error = degrees - imu.rotation()
        kP = 4
        left_motor.spin(FORWARD, 5 + error * kP, RPM)
        right_motor.spin(FORWARD, 5 - error * kP, RPM)
        
def turnToCardinal():
    """
    Uses the IMU to turn the robot by a specified number of degrees.
    """
    # imu.reset_rotation()
    # print("IMU rotation reset")

    while True:
        print("Target Rotation: " + str(degrees) + "Actual Rotation: " + str(imu.rotation()))
        degrees = round(imu.rotation() / 90) * 90
        print(degrees)
        if abs(degrees - imu.rotation()) < 0.5:
            print("Turn complete")
            left_motor.stop()
            right_motor.stop()
            
        error = degrees - imu.rotation()
        print(error)
        kP = 6
        left_motor.spin(FORWARD, 10 + error * kP, RPM)
        right_motor.spin(FORWARD, 10 - error * kP, RPM)

def followHeading(direction):
    """
    Adjusts driving to maintain a straight heading using the IMU.
    """
    error = imu.rotation()
    kP = 12.5
    base_speed_RPM = 200

    if direction == "REVERSE":
        left_motor.spin(REVERSE, base_speed_RPM - error * kP, RPM)
        right_motor.spin(REVERSE, base_speed_RPM + error * kP, RPM)
    else:
        left_motor.spin(FORWARD, base_speed_RPM - error * kP, RPM)
        right_motor.spin(FORWARD, base_speed_RPM + error * kP, RPM)

def goDistance(direction, distance):
    """
    Drives a specified distance while maintaining heading.
    """
    left_motor.reset_position()
    right_motor.reset_position()

    while encoderToInches(left_motor.position()) < distance:
        print("Distance Traveled: " + str(encoderToInches(left_motor.position())) + "inches")
        followHeading(direction)

    left_motor.stop()
    right_motor.stop()
    return True

def trackDistanceTraveled(distance):
    """
    Returns True if the robot has traveled the specified distance.
    """
    return encoderToInches(abs(left_motor.position(DEGREES))) > distance

def followLineWithIMU(direction, side):
    """
    Uses the reflectance sensors to follow a line, adjusting motor speeds accordingly.
    """
    front_error = right_front_reflectance.reflectivity() - left_front_reflectance.reflectivity()
    rear_error = right_back_reflectance.reflectivity() - left_back_reflectance.reflectivity()
    
    base_speed_RPM = 100
    front_kP = 0.5
    back_kP = 0.1

    front_left_motor_power = (base_speed_RPM - front_error * front_kP)
    # rear_left_motor_power = (base_speed_RPM - rear_error * back_kP)
    front_right_motor_power = (base_speed_RPM + front_error * front_kP)
    # rear_right_motor_power = (base_speed_RPM + rear_error * back_kP)

    # left_motor_power = front_left_motor_power + rear_left_motor_power
    # right_motor_power = front_right_motor_power + rear_right_motor_power

    degrees = round(imu.rotation() / 90) * 90
    error = degrees - imu.rotation()
    print(error)
    kP = 6
    left_motor_IMU_power = 10 + error * kP
    right_motor_IMU_power = 10 - error * kP


    left_motor.spin(FORWARD, front_left_motor_power + left_motor_IMU_power, RPM)
    right_motor.spin(FORWARD, front_right_motor_power + right_motor_IMU_power, RPM)
    

## STEP DEFINITIONS

# Define robot movement functions with parameters
def idle():
    left_motor.stop()
    right_motor.stop()
    lift_motor.stop()
    print("Robot is idle.")

def lining_by_distance(distance):
    print("Starting lining by distance: " + str(distance) + "inches")
    while not trackDistanceTraveled(distance):
        followLine("FORWARD", "FRONT")
        print("Degrees: " + str(left_motor.position(DEGREES)))
        print("Distance traveled: " + str(encoderToInches(left_motor.position(DEGREES))))
    return True  # Step completed successfully

def lining_by_distance_with_IMU(distance):
    print("Starting lining by distance: " + str(distance) + "inches")
    left_motor.reset_position()
    while not trackDistanceTraveled(distance):
        followLineWithIMU("FORWARD", "FRONT")
        print("Degrees: " + str(left_motor.position(DEGREES)))
        print("Distance traveled: " + str(encoderToInches(left_motor.position(DEGREES))))
    return True  # Step completed successfully

def turning(angle):
    print("Turning by " + str(angle) + " degrees")
    turnByDegrees(angle)
    return True  # Step completed successfully

def driving_to_fruit(fruit_type):
    while not driveToFruit(fruit_type):
      return False
    return True  # Step completed successfully

def harvesting_fruit():
    left_motor.stop()
    right_motor.stop()
    lift_motor.stop()

    right_motor.spin(FORWARD, 100, RPM)
    left_motor.spin_for(FORWARD, 2.75, TURNS, 100, RPM)
    right_motor.stop()

    print("Driven to fruit, harvesting next")
    
    lift_motor.spin_for(REVERSE, 1.5, TURNS, 50, RPM)
    right_motor.spin(REVERSE, 200, RPM)
    lift_motor.spin(FORWARD, 10, RPM)
    left_motor.spin_for(REVERSE, 5, TURNS, 200, RPM)
    lift_motor.stop()
    right_motor.stop()

    return True  # Step completed successfully

def lining_by_ultrasonic(threshold):
    front_sonar_timer.clear()
    while True:
        if controller.buttonX.pressing():  # Emergency override check
            idle()
            return False
        if front_sonar.distance(INCHES) < threshold:
            left_motor.stop()
            right_motor.stop()
            hopper_motor.spin_to_position(10)
            return True  # Step completed successfully
        else:
            followLine("FORWARD", "FRONT")

def lining_by_ultrasonic_with_IMU(threshold):
    front_sonar_timer.clear()
    while True:
        if front_sonar.distance(INCHES) < threshold:
            left_motor.stop()
            right_motor.stop()
            hopper_motor.spin_to_position(10)
            return True  # Step completed successfully
        else:
            followLineWithIMU("FORWARD", "FRONT")

def square_to_wall():
    while True:
        print("left_back_bumper: " + str(left_back_bumper.pressing()))
        print("right_back_bumper: " + str(right_back_bumper.pressing()))
        left_motor.spin(REVERSE, 200, RPM)
        right_motor.spin(REVERSE, 200, RPM)
        if left_back_bumper.pressing() and right_back_bumper.pressing():
            left_motor.stop()
            right_motor.stop()
            print("Squared to wall")
            return True

# Define step sequence with parameters
autonomous_steps = [
    (lining_by_distance_with_IMU, [15]),  # Move 20 inches forward
    (turning, [90]),  # Turn 90 degrees right
    (driving_to_fruit, ["orangutan"]),  # Drive towards fruit
    (harvesting_fruit, []),  # Harvest fruit
    
    (turning, [90]),  # Turn 180 degrees
    (square_to_wall, []),  # Square to wall
    
    (turning, [0]),  # Turn 180 degrees

    (lining_by_distance_with_IMU, [10]),  # Move 20 inches forward
    (turning, [90]),  # Turn 90 degrees right
    (driving_to_fruit, ["orangutan"]),  # Drive towards fruit
    (harvesting_fruit, []),  # Harvest fruit

    (turning, [90]),  # Turn 180 degrees
    (square_to_wall, []),  # Square to wall
    
    (turning, [180]),  # Turn 180 degrees
    (lining_by_ultrasonic, [5])  # Stop when ultrasonic sensor detects an object at 2 inches
    
    
    # (lining_by_distance_with_IMU, [2225]),  # Move 5 inches forward
    # (turning, [(imu.rotation() - ((imu.rotation() + 45) // 90 * 90))])
]


def printTelemetryToBrain():  
  brain.screen.print("current step " + str(current_step))
  brain.screen.new_line()
  brain.screen.print("rotation " + str(imu.rotation()))
  brain.screen.new_line()
  brain.screen.set_cursor(1, 1)

## Our main loop
while True:
    printTelemetryToBrain()
    
  # Execute autonomous sequence with emergency override
    while current_step < len(autonomous_steps):
        printTelemetryToBrain()
        if controller.buttonX.pressing():  # Emergency stop check before running each step
            print("ESTOPPED, going to idle.")
            idle()
            break

        step_function, args = autonomous_steps[current_step]
        success = step_function(*args)

        if not success:  # If a function returns False (e.g., emergency stop), exit loop
            break

        current_step += 1  # Move to the next step
    else:
        print("Waiting for commands... ") 
        if (controller.buttonL1.pressing() and not imu.is_calibrating()):
            current_step = 0
            print("Resetting to step 0")
