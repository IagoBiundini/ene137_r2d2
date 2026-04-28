#!/usr/bin/env python
import math

import rospy
from gazebo_msgs.srv import SetModelConfiguration
from sensor_msgs.msg import JointState
from std_msgs.msg import Float64


JOINT_NAME = "head_swivel"


class HeadController(object):
    def __init__(self):
        rospy.init_node("head_moviment_node")
        self.model_name = rospy.get_param("~model_name", "r2d2")

        self.joint_pub = rospy.Publisher("/joint_states", JointState, queue_size=10)

        rospy.loginfo("Aguardando servico /gazebo/set_model_configuration...")
        rospy.wait_for_service("/gazebo/set_model_configuration")
        self.set_model_configuration = rospy.ServiceProxy(
            "/gazebo/set_model_configuration", SetModelConfiguration
        )

        rospy.sleep(1.0)
        self.set_head_deg(0.0)

        rospy.Subscriber("/head_moviment", Float64, self.callback)
        rospy.loginfo("Controle da cabeca pronto em /head_moviment")
        rospy.spin()

    def publish_joint_state(self, angle_rad):
        joint = JointState()
        joint.header.stamp = rospy.Time.now()
        joint.name = [JOINT_NAME]
        joint.position = [angle_rad]
        joint.velocity = [0.0]
        joint.effort = [0.0]
        self.joint_pub.publish(joint)

    def set_head_deg(self, angle_deg):
        angle_deg = max(-180.0, min(180.0, angle_deg))
        angle_rad = math.radians(angle_deg)

        try:
            self.set_model_configuration(
                model_name=self.model_name,
                urdf_param_name="robot_description",
                joint_names=[JOINT_NAME],
                joint_positions=[angle_rad],
            )
            self.publish_joint_state(angle_rad)
        except rospy.ServiceException as exc:
            rospy.logwarn("Falha ao mover a cabeca no Gazebo: %s", exc)

    def callback(self, msg):
        self.set_head_deg(msg.data)


if __name__ == "__main__":
    HeadController()
