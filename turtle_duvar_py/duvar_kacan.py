import math

from geometry_msgs.msg import Twist
import rclpy
from rclpy.executors import ExternalShutdownException
from rclpy.node import Node
from turtlesim.msg import Pose


class DuvarKacan(Node):

    def __init__(self):
        super().__init__('duvar_kacan')

        self.declare_parameter('hiz', 2.0)
        self.declare_parameter('donus_hizi', 2.0)
        self.declare_parameter('alt_sinir', 1.0)
        self.declare_parameter('ust_sinir', 10.0)

        self.pose = None
        self.donuyor = False

        self.create_subscription(Pose, '/turtle1/pose', self.pose_geldi, 10)

        self.cmd_pub = self.create_publisher(Twist, '/turtle1/cmd_vel', 10)

        self.create_timer(0.1, self.kontrol)
        self.create_timer(1.0, self.konum_yazdir)

        self.get_logger().info('Duvardan kaçan kaplumbağa başladı.')

    def pose_geldi(self, msg):
        self.pose = msg

    def sinir_disinda_mi(self, x, y):
        alt = self.get_parameter('alt_sinir').value
        ust = self.get_parameter('ust_sinir').value
        return x < alt or x > ust or y < alt or y > ust

    def iceri_bakiyor_mu(self, x, y, theta):
        alt = self.get_parameter('alt_sinir').value
        ust = self.get_parameter('ust_sinir').value
        yon_x = math.cos(theta)
        yon_y = math.sin(theta)
        esik = 0.5

        if x < alt and yon_x < esik:
            return False
        if x > ust and yon_x > -esik:
            return False
        if y < alt and yon_y < esik:
            return False
        if y > ust and yon_y > -esik:
            return False
        return True

    def kontrol(self):
        if self.pose is None:
            return

        x, y, theta = self.pose.x, self.pose.y, self.pose.theta
        komut = Twist()

        if self.sinir_disinda_mi(x, y) and not self.iceri_bakiyor_mu(x, y, theta):
            komut.angular.z = self.get_parameter('donus_hizi').value
            if not self.donuyor:
                self.get_logger().warn(
                    f'Sınıra gelindi (x={x:.2f}, y={y:.2f}), dönülüyor...')
            self.donuyor = True
        else:
            komut.linear.x = self.get_parameter('hiz').value
            self.donuyor = False

        self.cmd_pub.publish(komut)

    def konum_yazdir(self):
        if self.pose is None:
            self.get_logger().info('/turtle1/pose bekleniyor...')
            return
        self.get_logger().info(
            f'Konum: x={self.pose.x:.2f}, y={self.pose.y:.2f}, '
            f'theta={self.pose.theta:.2f}')


def main(args=None):
    rclpy.init(args=args)
    node = DuvarKacan()
    try:
        rclpy.spin(node)
    except (KeyboardInterrupt, ExternalShutdownException):
        pass
    finally:
        if rclpy.ok():
            node.cmd_pub.publish(Twist())
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == '__main__':
    main()
