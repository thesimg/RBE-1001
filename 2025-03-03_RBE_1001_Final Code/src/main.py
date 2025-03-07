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

## Define the camera
Vision__LIME = Signature (1, -6069, -4855, -5462, -3131, -2407, -2769, 3.900, 0)
Vision__LEMON = Signature (2, 131, 425, 278, -3915, -3429, -3672, 7.400, 0)
Vision__ORANGUTAN = Signature (3, 5323, 6263, 5793, -2717, -2111, -2414, 5.9, 0)

camera = Vision (Ports.PORT7, 50, Vision__LEMON, Vision__LIME, Vision__ORANGUTAN)

# Sensor Declarations
front_sonar = Sonar(brain.three_wire_port.e)
front_sonar_timer = Timer()

lastTwentySonarReadings = [100] * 20
avgSonarDistance = sum(lastTwentySonarReadings) / len(lastTwentySonarReadings)

right_front_reflectance = Line(brain.three_wire_port.b)
left_front_reflectance = Line(brain.three_wire_port.a)

right_back_reflectance = Line(brain.three_wire_port.c)
left_back_reflectance = Line(brain.three_wire_port.d)

imu = Inertial(Ports.PORT6)

# calibrate imu
imu.calibrate()
while imu.is_calibrating(): # wait 2 seconds for imu to calibrate
    # print("Calibrating IMU...")
    wait(100)  # wait 100ms to avoid flooding the console
print("IMU calibrated")

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
        # print("Largest object - Width:", camera.largest_object().width, "Height:", camera.largest_object().height)
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

            # print("Height: " + str(object_height) + "Left Power: " + str(left_power) + "Right Power: " + str(right_power))

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

            # print("Object Y: " + str(object_y) + "Lift Power: " + str(lift_power))

            # Stop when the object is close enough and centered
            if object_height > 120 and abs(x_error) < 5:
                print("Object is close enough")
                return True
        else:
            # print("Object is too far away, adjusting position")
            left_motor.spin(REVERSE, 50, RPM)
            right_motor.spin(FORWARD, 50, RPM)
            lift_motor.stop()
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
    return right_front_reflectance.reflectivity() > 70 and left_front_reflectance.reflectivity() > 70

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
        # print("Target Rotation: " + str(degrees) + "Actual Rotation: " + str(imu.rotation()))
        
        if abs(degrees - imu.rotation()) < 0.5:
            print("Turn complete")
            left_motor.stop()
            right_motor.stop()
            return True

        error = degrees - imu.rotation()
        kP = 6
        left_motor.spin(FORWARD, 5 + error * kP, RPM)
        right_motor.spin(FORWARD, 5 - error * kP, RPM)
        
        
def turnByDegreesFromWall(degrees):
    """
    Uses the IMU to turn the robot by a specified number of degrees.
    """
    # imu.reset_rotation()
    # print("IMU rotation reset")

    while True:
        # print("Target Rotation: " + str(degrees) + "Actual Rotation: " + str(imu.rotation()))
        
        if abs(degrees - imu.rotation()) < 0.5:
            print("Turn from wall complete")
            left_motor.stop()
            right_motor.stop()
            return True

        error = degrees - imu.rotation()
        kP = 6
        baseFeedforwardRPM = 30
        turnBoost = 3
        turnReduce = 0.4
        if(error > 0):
            left_motor.spin(FORWARD, baseFeedforwardRPM + error * kP * turnBoost, RPM)
            right_motor.spin(FORWARD, baseFeedforwardRPM - error * kP * turnReduce, RPM)
        else:
            left_motor.spin(FORWARD, baseFeedforwardRPM + error * kP * turnReduce, RPM)
            right_motor.spin(FORWARD, baseFeedforwardRPM - error * kP * turnBoost, RPM)
        
def turnToCardinal():
    """
    Uses the IMU to turn the robot by a specified number of degrees.
    """
    # imu.reset_rotation()
    # print("IMU rotation reset")

    while True:
        degrees = round(imu.rotation() / 90) * 90
        # print("Target Rotation: " + str(degrees) + "Actual Rotation: " + str(imu.rotation()))
        if abs(degrees - imu.rotation()) < 0.5:
            print("Turn complete")
            left_motor.stop()
            right_motor.stop()
            return True
            
        error = degrees - imu.rotation()
        # print(error)
        kP = 6
        left_motor.spin(FORWARD, 10 + error * kP, RPM)
        right_motor.spin(FORWARD, 10 - error * kP, RPM)

def followHeading(direction, targetHeading):
    """
    Adjusts driving to maintain a straight heading using the IMU.
    """
    error = imu.rotation() - targetHeading
    kP = 12.5
    base_speed_RPM = 200

    # print("Target Rotation: " + str(targetHeading) + "Actual Rotation: " + str(imu.rotation()))
    # print("Error: " + str(error))
    
    
    if direction == "REVERSE":
        left_motor.spin(REVERSE, base_speed_RPM - error * kP, RPM)
        right_motor.spin(REVERSE, base_speed_RPM + error * kP, RPM)
    else:
        left_motor.spin(FORWARD, base_speed_RPM - error * kP, RPM)
        right_motor.spin(FORWARD, base_speed_RPM + error * kP, RPM)

def goDistance(direction, distance, orientation):
    """
    Drives a specified distance while maintaining heading.
    """
    left_motor.reset_position()
    right_motor.reset_position()

    while encoderToInches(left_motor.position()) < distance:
        # print("Distance Traveled: " + str(encoderToInches(left_motor.position())) + "inches")
        followHeading(direction, orientation)

    left_motor.stop()
    right_motor.stop()
    return True

def trackDistanceTraveled(distance):
    """
    Returns True if the robot has traveled the specified distance.
    """
    return encoderToInches(abs(left_motor.position(DEGREES))) > distance

def followLineWithIMU():
    """
    Uses the reflectance sensors to follow a line, adjusting motor speeds accordingly.
    """
    front_error = right_front_reflectance.reflectivity() - left_front_reflectance.reflectivity()
    rear_error = right_back_reflectance.reflectivity() - left_back_reflectance.reflectivity()
    
    base_speed_RPM = 150
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
    # print(error)
    kP = 6
    left_motor_IMU_power = 10 + error * kP
    right_motor_IMU_power = 10 - error * kP


    left_motor.spin(FORWARD, front_left_motor_power + left_motor_IMU_power, RPM)
    right_motor.spin(FORWARD, front_right_motor_power + right_motor_IMU_power, RPM)
    

def calculateAvgSonar():
    global avgSonarDistance
    lastTwentySonarReadings.pop(0)
    lastTwentySonarReadings.append(front_sonar.distance(INCHES))
    avgSonarDistance = sum(lastTwentySonarReadings) / len(lastTwentySonarReadings)
    # print("Average sonar distance: " + str(avgSonarDistance))

## STEP DEFINITIONS

# Define robot movement functions with parameters
def idle():
    left_motor.stop()
    right_motor.stop()
    lift_motor.stop()
    print("Robot is idle.")
    return "IDLE"  # Return value to signify idle state

def lining_by_distance(distance):
    # print("Starting lining by distance: " + str(distance) + "inches")
    left_motor.reset_position()  # Reset position counter
    while not trackDistanceTraveled(distance):
        followLine("FORWARD", "FRONT")
        # print("Degrees: " + str(left_motor.position(DEGREES)))
        # print("Distance traveled: " + str(encoderToInches(left_motor.position(DEGREES))))
    return True  # Step completed successfully

def lining_by_distance_with_IMU(distance):
    # print("Starting lining by distance: " + str(distance) + "inches")
    left_motor.reset_position()
    while not trackDistanceTraveled(distance):
        followLineWithIMU()
        # print("Degrees: " + str(left_motor.position(DEGREES)))
        # print("Distance traveled: " + str(encoderToInches(left_motor.position(DEGREES))))
    left_motor.stop()
    right_motor.stop()
    return True  # Step completed successfully

def turning(angle):
    # print("Turning by " + str(angle) + " degrees")
    turnByDegrees(angle)
    return True  # Step completed successfully

def turning_from_wall(angle):
    # print("Turning by " + str(angle) + " degrees")
    turnByDegreesFromWall(angle)
    return True  # Step completed successfully

def driving_to_fruit(fruit_type):
    while not driveToFruit(fruit_type):
        pass  # Keep trying until successful
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
    lift_motor.spin(FORWARD, 80, RPM)
    left_motor.spin_for(REVERSE, 5, TURNS, 200, RPM)
    lift_motor.stop()
    right_motor.stop()

    return True  # Step completed successfully

# def lining_by_ultrasonic(threshold):
#     front_sonar_timer.clear()
#     while front_sonar.distance(INCHES) >= threshold:
#         followLine("FORWARD", "FRONT")
    
#     left_motor.stop()
#     right_motor.stop()
#     # hopper_motor.spin_to_position(10)
#     return True  # Step completed successfully

previousSonarDistance = 0
newSonarDistance = 0
def lining_by_ultrasonic_with_IMU(threshold):
    print("Starting lining by ultrasonic: " + str(threshold) + "inches")
    print("Distance: " + str(front_sonar.distance(INCHES)))
    
    # print("Average sonar distance: " + str(avgSonarDistance)
    # global previousSonarDistance
    # global newSonarDistance
    
    # previousSonarDistance = newSonarDistance
    # newSonarDistance = front_sonar.distance(INCHES)
    
    while front_sonar.distance(INCHES) >= threshold:
        
        # previousSonarDistance = newSonarDistance
        # newSonarDistance = front_sonar.distance(INCHES)
        # print("New sonar distance: " + str(newSonarDistance))
        # print("Previous sonar distance: " + str(previousSonarDistance))
        
        # print("lininy by ultrasonic " + str(avgSonarDistance) )
        # calculateAvgSonar()
        print("Distance: " + str(front_sonar.distance(INCHES)))
        
        followLineWithIMU()
    
    print("at ultrasonic threshold")
    left_motor.stop()
    right_motor.stop()
    return True  # Step completed successfully

def square_to_wall():
    while True:
        # print("left_back_bumper: " + str(left_back_bumper.pressing()))
        # print("right_back_bumper: " + str(right_back_bumper.pressing()))
        left_motor.spin(REVERSE, 200, RPM)
        right_motor.spin(REVERSE, 200, RPM)
        if left_back_bumper.pressing() and right_back_bumper.pressing():
            left_motor.stop()
            right_motor.stop()
            print("Squared to wall")
            return True

def deposit_fruit():
    hopper_motor.spin_to_position(10)
    right_motor.spin(REVERSE, 200, RPM)
    left_motor.spin_for(REVERSE, 1, TURNS, 200, RPM)
    right_motor.stop()
    hopper_motor.spin_to_position(75)
    return True  # Step completed successfully

def driving_to_line(targetHeading):
    left_motor.reset_position()
    print("driving to line")
    # print("right front reflectance: " + str(right_front_reflectance.reflectivity()))
    # print("left front reflectance: " + str(left_front_reflectance.reflectivity()))
    while not detectBothReflecting():
        followHeading("FORWARD", targetHeading)
        # print("Degrees: " + str(left_motor.position(DEGREES)))
        # print("Distance traveled: " + str(encoderToInches(left_motor.position(DEGREES))))
    right_motor.stop()
    left_motor.stop()
    return True  # Step completed successfully

def drive_forward_onto_line():
    right_motor.spin(FORWARD, 200, RPM)
    left_motor.spin_for(FORWARD, 3.5, TURNS, 200, RPM)
    right_motor.stop()
    return True

def recalibrate_imu():
    imu.calibrate()
    while imu.is_calibrating(): # wait 2 seconds for imu to calibrate
        # print("Calibrating IMU...")
        wait(100)  # wait 100ms to avoid flooding the console
    imu.reset_rotation()
    print("IMU recalibrated")
    return True  # Step completed successfully

def printTelemetry(toPrint):
    print("telemetry: " + str(toPrint))
    wait(500)  # wait 100ms to avoid flooding the console
    return True

def wait500ms():
    wait(500)  # wait 100ms to avoid flooding the console
    return True

# Define step sequence with parameters
autonomous_steps = [
    
    # LEMON LEMON LEMON LEMON 
    
   
    (lining_by_distance_with_IMU, [15]),  # Move 20 inches forward
    (turning, [-20]),
    (drive_forward_onto_line, []),  # Move onto line
    
    
    (lining_by_distance_with_IMU, [6]),  # Move 20 inches forward
    (turning_from_wall, [90]),  # Turn 90 degrees right
    (driving_to_fruit, ["lemon"]),  # Drive towards fruit
    (harvesting_fruit, []),  # Harvest fruit
    
    (turning, [90]),  # Turn 180 degrees
    (square_to_wall, []),  # Square to wall
    
    (turning_from_wall, [0]),  # Turn 180 degrees

    (lining_by_distance_with_IMU, [8]),  # Move 20 inches forward
    (turning_from_wall, [90]),  # Turn 90 degrees right
    (driving_to_fruit, ["lemon"]),  # Drive towards fruit
    (harvesting_fruit, []),  # Harvest fruit

    (turning, [90]),  # Turn 180 degrees
    (square_to_wall, []),  # Square to wall
    
    (turning_from_wall, [180]),  # Turn 180 degrees
    (lining_by_ultrasonic_with_IMU, [14]),  # Stop when ultrasonic sensor detects an object at 2 inches
    
    (turning, [90]),  # Turn 180 degrees
    (lining_by_distance_with_IMU, [24]),  # Stop when ultrasonic sensor detects an object at 2 inches
    (turning_from_wall, [180]),  # Turn 180 degrees
    (lining_by_ultrasonic_with_IMU, [2]),  # Move 20 inches forward
    (deposit_fruit, []),  # Move to deposit fruit
    
    (turning, [270]),  # Turn 90 degrees right
    (driving_to_line, [270]),  # Drive to line
    (turning, [350]),  # Turn 90 degrees right   
    (square_to_wall, []),  # Square to wall
   
    (recalibrate_imu, []),  # Recalibrate IMU
   
   
   
   
    # # RECALIBRAITON
   
    (lining_by_distance_with_IMU, [15]),  # Move 20 inches forward
    (turning, [-20]),
    (drive_forward_onto_line, []),  # Move onto line
    
    
    
    
    # LIME LIME LIME LIME
    
    (lining_by_distance_with_IMU, [46]),  # Move 20 inches forward
    (turning_from_wall, [90]),  # Turn 90 degrees right
    (driving_to_fruit, ["lime"]),  # Drive towards fruit
    (harvesting_fruit, []),  # Harvest fruit
    
    (turning, [90]),  # Turn 180 degrees
    (square_to_wall, []),  # Square to wall
    
    (turning_from_wall, [0]),  # Turn 180 degrees

    (lining_by_distance_with_IMU, [8]),  # Move 20 inches forward
    (turning_from_wall, [90]),  # Turn 90 degrees right
    (driving_to_fruit, ["lime"]),  # Drive towards fruit
    (harvesting_fruit, []),  # Harvest fruit

    (turning, [90]),  # Turn 180 degrees
    (square_to_wall, []),  # Square to wall
    
    (turning_from_wall, [180]),  # Turn 180 degrees
    (printTelemetry, ["starting lining by ultrasonic"]),
    (lining_by_distance_with_IMU, [35]),  # Move 20 inches forward
    (lining_by_ultrasonic_with_IMU, [14]),  # Stop when ultrasonic sensor detects an object at 2 inches
    (printTelemetry, ["finished lining by ultrasonic"]),
    
    (printTelemetry, ["turning to 90"]),
    (turning, [90]),  # Turn 180 degrees
    (printTelemetry, ["starting lining by distance"]),
    (lining_by_distance_with_IMU, [24]),  # Stop when ultrasonic sensor detects an object at 2 inches
    (turning_from_wall, [180]),  # Turn 180 degrees
    (lining_by_ultrasonic_with_IMU, [2]),  # Move 20 inches forward
    (deposit_fruit, []),  # Move to deposit fruit
    
    (turning, [270]),  # Turn 90 degrees right
    (driving_to_line, [270]),  # Drive to line
    (turning, [350]),  # Turn 90 degrees right   
    (square_to_wall, []),  # Square to wall
   
    (recalibrate_imu, []),  # Recalibrate IMU
    
   
   
    # RECALIBRAITON
   
    (lining_by_distance_with_IMU, [15]),  # Move 20 inches forward
    (turning, [-20]),
    (drive_forward_onto_line, []),  # Move onto line
    
    
    
    
    # ORANGUTAN ORANGUTAN ORANGUTAN ORANGUTAN
    
    (lining_by_distance_with_IMU, [80]),  # Move 20 inches forward
    (turning_from_wall, [90]),  # Turn 90 degrees right
    (driving_to_fruit, ["orangutan"]),  # Drive towards fruit
    (harvesting_fruit, []),  # Harvest fruit
    
    (turning, [90]),  # Turn 180 degrees
    (square_to_wall, []),  # Square to wall
    
    (turning_from_wall, [0]),  # Turn 180 degrees

    (lining_by_distance_with_IMU, [8]),  # Move 20 inches forward
    (turning_from_wall, [90]),  # Turn 90 degrees right
    (driving_to_fruit, ["orangutan"]),  # Drive towards fruit
    (harvesting_fruit, []),  # Harvest fruit

    (turning, [90]),  # Turn 180 degrees
    (square_to_wall, []),  # Square to wall
    
    (turning_from_wall, [180]),  # Turn 180 degrees
    (lining_by_distance_with_IMU, [70]),  # Move 20 inches forward
    # (wait500ms, []),  # Wait 500ms
    (lining_by_ultrasonic_with_IMU, [14]),  # Stop when ultrasonic sensor detects an object at 2 inches
    
    (printTelemetry, ["turning to 90"]),
    (turning, [90]),  # Turn 180 degrees
    (printTelemetry, ["starting lining by distance"]),
    (lining_by_distance_with_IMU, [24]),  # Stop when ultrasonic sensor detects an object at 2 inches
    (turning_from_wall, [180]),  # Turn 180 degrees
    (lining_by_ultrasonic_with_IMU, [2]),  # Move 20 inches forward
    (deposit_fruit, []),  # Move to deposit fruit
    
    (turning, [270]),  # Turn 90 degrees right
    (driving_to_line, [270]),  # Drive to line
    (turning, [350]),  # Turn 90 degrees right   
    (square_to_wall, []),  # Square to wall
   
    (recalibrate_imu, []),  # Recalibrate IMU
    
    
    
    
    
    # TESTING
    
    # (turning, [270]),  # Turn 90 degrees right
    # (driving_to_line, [270]),  # Drive to line
    
    # (lining_by_distance_with_IMU, [5]),  # Move 20 inches forward
    # (turning_from_wall, [90]),  # Turn 90 degrees right
    # (square_to_wall, []),  # Square to wall
    # (lining_by_distance_with_IMU, [5]),  # Move 20 inches forward
    
    # (lining_by_distance_with_IMU, [2225]),  # Move 5 inches forward
    # (turning, [(imu.rotation() - ((imu.rotation() + 45) // 90 * 90))])
    
    # (lining_by_ultrasonic_with_IMU, [2]),  # Move 20 inches forward
]

# Define state constants
IDLE = "IDLE"  # Define IDLE constant

def printTelemetryToBrain():  
    brain.screen.print("current step " + str(current_step))
    brain.screen.new_line()
    brain.screen.print("rotation " + str(imu.rotation()))
    brain.screen.new_line()
    brain.screen.print("right fron reflectance " + str(right_front_reflectance.reflectivity()))
    brain.screen.new_line()
    brain.screen.print("left front reflectance " + str(left_front_reflectance.reflectivity()))
    brain.screen.new_line()
    brain.screen.print("right back reflectance " + str(right_back_reflectance.reflectivity()))
    brain.screen.new_line()
    brain.screen.print("left back reflectance " + str(left_back_reflectance.reflectivity()))
    brain.screen.new_line()
    brain.screen.print("left bumper " + str(left_back_bumper.pressing()))
    brain.screen.new_line()
    brain.screen.print("right bumper " + str(right_back_bumper.pressing()))
    brain.screen.new_line()
    brain.screen.print("front sonar " + str(front_sonar.distance(INCHES)))
    brain.screen.new_line()
    brain.screen.print("average front sonar " + str(avgSonarDistance))
    brain.screen.new_line()
    brain.screen.set_cursor(1, 1)

## Our main loop
while True:
    printTelemetryToBrain()
    
    
    # Check for emergency stop first
    if controller.buttonX.pressing():
        print("ESTOPPED, going to idle.")
        idle()
        # Continue the main loop, which will restart from the top
        continue
    
    # Execute autonomous sequence
    if current_step < len(autonomous_steps):
        printTelemetryToBrain()
        
        step_function, args = autonomous_steps[current_step]
        success = step_function(*args)
        
        if success == IDLE:  # Check if we need to go to idle state
            print("Entering IDLE state.")
            continue
        elif success:  # If step completed successfully
            current_step += 1  # Move to the next step
        else:
            # Handle failure in a non-emergency way if needed
            print("Step failed, retrying.")
    else:
        printTelemetryToBrain()
        # print("Waiting for commands... ")
        if (controller.buttonL1.pressing() and not imu.is_calibrating()):
            current_step = 0
            print("Resetting to step 0")