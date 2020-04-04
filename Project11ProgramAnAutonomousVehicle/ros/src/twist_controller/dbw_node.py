#!/usr/bin/env python

import rospy
from std_msgs.msg import Bool
from dbw_mkz_msgs.msg import ThrottleCmd, SteeringCmd, BrakeCmd, SteeringReport
from geometry_msgs.msg import TwistStamped
import math

from twist_controller import Controller

'''
You can build this node only after you have built (or partially built) the `waypoint_updater` node.

You will subscribe to `/twist_cmd` message which provides the proposed linear and angular velocities.
You can subscribe to any other message that you find important or refer to the document for list
of messages subscribed to by the reference implementation of this node.

One thing to keep in mind while building this node and the `twist_controller` class is the status
of `dbw_enabled`. While in the simulator, its enabled all the time, in the real car, that will
not be the case. This may cause your PID controller to accumulate error because the car could
temporarily be driven by a human instead of your controller.

We have provided two launch files with this node. Vehicle specific values (like vehicle_mass,
wheel_base) etc should not be altered in these files.

We have also provided some reference implementations for PID controller and other utility classes.
You are free to use them or build your own.

Once you have the proposed throttle, brake, and steer values, publish it on the various publishers
that we have created in the `__init__` function.

'''
# This parameter defines the frquency at which throttle, brake
# and steering command are send to the vehicle. It must be equal
# or larger than 10 Hz. Changing this parameter changes the
# closed loop behavior, i.e. if & how the vehicle follows the
# reference trajectory. If this paramter is changed, the
# controller parameters KP, KI, and KD may become invalid.
TWIST_CONTROLLER_UPDATE_FREQUENCY = 10

class DBWNode(object):
    def __init__(self):
        rospy.init_node('dbw_node')

        self.controller = Controller(
            vehicle_mass=rospy.get_param('~vehicle_mass', 1736.35),
            fuel_capacity=rospy.get_param('~fuel_capacity', 13.5),
            brake_deadband=rospy.get_param('~brake_deadband', .1),
            decel_limit=rospy.get_param('~decel_limit', -5),
            accel_limit=rospy.get_param('~accel_limit', 1.),
            wheel_radius=rospy.get_param('~wheel_radius', 0.2413),
            wheel_base=rospy.get_param('~wheel_base', 2.8498),
            steer_ratio=rospy.get_param('~steer_ratio', 14.8),
            max_lat_accel=rospy.get_param('~max_lat_accel', 3.),
            max_steer_angle=rospy.get_param('~max_steer_angle', 8.))

        self.steer_pub = rospy.Publisher('/vehicle/steering_cmd',
                                         SteeringCmd, queue_size=1)
        self.throttle_pub = rospy.Publisher('/vehicle/throttle_cmd',
                                            ThrottleCmd, queue_size=1)
        self.brake_pub = rospy.Publisher('/vehicle/brake_cmd',
                                         BrakeCmd, queue_size=1)

        rospy.Subscriber('/vehicle/dbw_enabled', Bool, self.dbw_enabled_cb)
        rospy.Subscriber('/twist_cmd', TwistStamped, self.twist_cb)
        rospy.Subscriber('/current_velocity', TwistStamped, self.velocity_cb)

        self.current_vel = None
        self.current_ang_vel = None
        self.linear_vel = None
        self.angular_vel = None
        self.dbw_enabled = True
        self.throttle = self.steering = self.brake = 0

        self.loop()

    def loop(self):
        rate = rospy.Rate(TWIST_CONTROLLER_UPDATE_FREQUENCY)
        while not rospy.is_shutdown():
            if not None in (self.current_vel,
                            self.linear_vel,
                            self.angular_vel):
                (self.throttle,
                 self.brake,
                 self.steering) = self.controller.control(self.current_vel,
                                                          self.dbw_enabled,
                                                          self.linear_vel,
                                                          self.angular_vel)
            if self.dbw_enabled:
                rospy.loginfo("dbw_node.py: Call to dbw_node, controller output: throttle=%.3f, brake=%.3f, steering=%.3f", self.throttle, self.brake, self.steering)
                self.publish(self.throttle, self.brake, self.steering)
            else:
                rospy.loginfo("dbw_node.py: Call to dbw_node.py, drive-by-wire is disabled.")
            rate.sleep()

    def dbw_enabled_cb(self, msg):
        self.dbw_enabled = msg
        rospy.loginfo("dbw_node.py: Drive by wire was turned: {}".format("on" if self.dbw_enabled else "off"))

    def twist_cb(self, msg):
        self.linear_vel = msg.twist.linear.x
        self.angular_vel = msg.twist.angular.z

    def velocity_cb(self, msg):
        self.current_vel = msg.twist.linear.x

    def publish(self, throttle, brake, steer):
        tcmd = ThrottleCmd()
        tcmd.enable = True
        tcmd.pedal_cmd_type = ThrottleCmd.CMD_PERCENT
        tcmd.pedal_cmd = throttle
        self.throttle_pub.publish(tcmd)

        scmd = SteeringCmd()
        scmd.enable = True
        scmd.steering_wheel_angle_cmd = steer
        self.steer_pub.publish(scmd)

        bcmd = BrakeCmd()
        bcmd.enable = True
        bcmd.pedal_cmd_type = BrakeCmd.CMD_TORQUE
        bcmd.pedal_cmd = brake
        self.brake_pub.publish(bcmd)


if __name__ == '__main__':
    DBWNode()
