#!/usr/bin/env python
import os
import select
import sys
import termios
import tty

import rospy
from geometry_msgs.msg import Twist
from std_msgs.msg import Float64


LINEAR_SPEED = 0.4
ANGULAR_SPEED = 1.0
HEAD_STEP_DEG = 10.0
HEAD_MIN_DEG = -180.0
HEAD_MAX_DEG = 180.0
KEY_HOLD_TIMEOUT = 0.15


def clamp(value, lower, upper):
    return max(lower, min(upper, value))


def read_key():
    dr, _, _ = select.select([sys.stdin], [], [], 0.1)
    if not dr:
        return None

    first = os.read(sys.stdin.fileno(), 1).decode("utf-8", errors="ignore")
    if first != "\x1b":
        return first

    if select.select([sys.stdin], [], [], 0.03)[0]:
        second = os.read(sys.stdin.fileno(), 1).decode("utf-8", errors="ignore")
        if second == "[" and select.select([sys.stdin], [], [], 0.03)[0]:
            third = os.read(sys.stdin.fileno(), 1).decode("utf-8", errors="ignore")
            return "\x1b[" + third
        return first + second

    return first


def print_help():
    print("")
    print("Controle do R2D2")
    print("----------------")
    print("Base:")
    print("  W/S      frente / tras")
    print("  A/D      gira esquerda / direita")
    print("  ESPACO   parar")
    print("")
    print("Cabeca:")
    print("  <-  ->   gira 10 graus")
    print("  cima     centraliza em 0 graus")
    print("  baixo    vai para 180 graus")
    print("")
    print("Geral:")
    print("  Q        sair")
    print("")


def main():
    rospy.init_node("r2d2_keyboard_control")

    cmd_pub = rospy.Publisher("/cmd_vel", Twist, queue_size=10)
    head_pub = rospy.Publisher("/head_moviment", Float64, queue_size=10)

    linear = 0.0
    angular = 0.0
    head_deg = 0.0
    last_motion_time = 0.0

    print_help()
    head_pub.publish(Float64(head_deg))
    settings = termios.tcgetattr(sys.stdin)
    tty.setraw(sys.stdin.fileno())

    try:
        while not rospy.is_shutdown():
            key = read_key()
            now = rospy.get_time()

            if key is not None:
                if key == "q":
                    break
                elif key == "w":
                    linear = LINEAR_SPEED
                    angular = 0.0
                    last_motion_time = now
                elif key == "s":
                    linear = -LINEAR_SPEED
                    angular = 0.0
                    last_motion_time = now
                elif key == "a":
                    linear = 0.0
                    angular = ANGULAR_SPEED
                    last_motion_time = now
                elif key == "d":
                    linear = 0.0
                    angular = -ANGULAR_SPEED
                    last_motion_time = now
                elif key == " ":
                    linear = 0.0
                    angular = 0.0
                elif key == "\x1b[D":
                    head_deg = clamp(head_deg - HEAD_STEP_DEG, HEAD_MIN_DEG, HEAD_MAX_DEG)
                    head_pub.publish(Float64(head_deg))
                elif key == "\x1b[C":
                    head_deg = clamp(head_deg + HEAD_STEP_DEG, HEAD_MIN_DEG, HEAD_MAX_DEG)
                    head_pub.publish(Float64(head_deg))
                elif key == "\x1b[A":
                    head_deg = 0.0
                    head_pub.publish(Float64(head_deg))
                elif key == "\x1b[B":
                    head_deg = 180.0
                    head_pub.publish(Float64(head_deg))

            if (linear != 0.0 or angular != 0.0) and (now - last_motion_time) > KEY_HOLD_TIMEOUT:
                linear = 0.0
                angular = 0.0

            twist = Twist()
            twist.linear.x = linear
            twist.angular.z = angular
            cmd_pub.publish(twist)

            sys.stdout.write(
                "\r\033[KBase [lin: {:+.2f} | ang: {:+.2f}]   Cabeca [{:+.1f} deg]".format(
                    linear, angular, head_deg
                )
            )
            sys.stdout.flush()

    finally:
        twist = Twist()
        cmd_pub.publish(twist)
        head_pub.publish(Float64(head_deg))
        termios.tcsetattr(sys.stdin, termios.TCSADRAIN, settings)
        sys.stdout.write("\r\033[K")
        sys.stdout.flush()
        print("")


if __name__ == "__main__":
    main()
