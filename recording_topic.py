import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image
from geometry_msgs.msg import PoseStamped
from cv_bridge import CvBridge
import cv2
import os
import json

class ImagePoseSaver(Node):
    def __init__(self):
        super().__init__('image_pose_saver')

        # 이미지 저장 경로, 만약 폴더가 없다면 생성
        self.image_dir = '/root/ORB-SLAM3-ROS2-Docker/data/images'
        os.makedirs(self.image_dir, exist_ok=True)

        # 포즈 저장 경로
        self.pose_dir = '/root/ORB-SLAM3-ROS2-Docker/data/poses'
        os.makedirs(self.pose_dir, exist_ok=True)

        self.bridge = CvBridge()

        # 구독자
        self.create_subscription(Image, '/camera/camera/color/image_raw', self.image_callback, 10)
        self.create_subscription(PoseStamped, '/robot_pose_slam', self.pose_callback, 10)

        # 저장용 딕셔너리 (타임스탬프별 포즈 저장)
        self.pose_data = {}

    def image_callback(self, msg: Image):
        # 이미지 저장 (타임스탬프 기준으로 파일명)
        timestamp = msg.header.stamp.sec + msg.header.stamp.nanosec * 1e-9
        filename = os.path.join(self.image_dir, f'{timestamp:.9f}.jpg')

        # 이미지 변환
        cv_image = self.bridge.imgmsg_to_cv2(msg, desired_encoding='bgr8')
        cv2.imwrite(filename, cv_image)

        self.get_logger().info(f'Image saved: {filename}')

        # 포즈가 이미 저장되어 있으면 json 파일 생성
        if str(timestamp) in self.pose_data:
            pose_filename = os.path.join(self.pose_dir, f'{timestamp:.9f}.json')
            with open(pose_filename, 'w') as f:
                json.dump(self.pose_data[str(timestamp)], f, indent=2)
            self.get_logger().info(f'Pose saved: {pose_filename}')
            del self.pose_data[str(timestamp)]

    def pose_callback(self, msg: PoseStamped):
        # 포즈 메시지 저장 (딕셔너리 형태)
        timestamp = msg.header.stamp.sec + msg.header.stamp.nanosec * 1e-9
        pose_dict = {
            'header': {
                'stamp': {
                    'sec': msg.header.stamp.sec,
                    'nanosec': msg.header.stamp.nanosec,
                },
                'frame_id': msg.header.frame_id,
            },
            'pose': {
                'position': {
                    'x': msg.pose.position.x,
                    'y': msg.pose.position.y,
                    'z': msg.pose.position.z,
                },
                'orientation': {
                    'x': msg.pose.orientation.x,
                    'y': msg.pose.orientation.y,
                    'z': msg.pose.orientation.z,
                    'w': msg.pose.orientation.w,
                }
            }
        }

        # 이미지보다 먼저 오는 경우 저장
        self.pose_data[str(timestamp)] = pose_dict

        # 이미지가 이미 저장되어 있으면 json 파일 생성
        image_path = os.path.join(self.image_dir, f'{timestamp:.9f}.jpg')
        if os.path.exists(image_path):
            pose_filename = os.path.join(self.pose_dir, f'{timestamp:.9f}.json')
            with open(pose_filename, 'w') as f:
                json.dump(pose_dict, f, indent=2)
            self.get_logger().info(f'Pose saved: {pose_filename}')
            del self.pose_data[str(timestamp)]

def main(args=None):
    rclpy.init(args=args)
    node = ImagePoseSaver()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()
# import rclpy
# from rclpy.node import Node
# from sensor_msgs.msg import Image
# from geometry_msgs.msg import PoseStamped
# from slam_msgs.msg import MapData   # MapData 메시지 import
# from cv_bridge import CvBridge
# import cv2
# import os
# import json

# class ImagePoseSaver(Node):
#     def __init__(self):
#         super().__init__('image_pose_saver')

#         # 이미지 저장 경로, 없으면 생성
#         self.image_dir = '/root/ORB-SLAM3-ROS2-Docker/data/images'
#         os.makedirs(self.image_dir, exist_ok=True)

#         # 포즈 저장 경로
#         self.pose_dir = '/root/ORB-SLAM3-ROS2-Docker/data/poses'
#         os.makedirs(self.pose_dir, exist_ok=True)

#         # 맵 데이터 저장 경로
#         self.map_dir = '/root/ORB-SLAM3-ROS2-Docker/data/maps'
#         os.makedirs(self.map_dir, exist_ok=True)

#         self.bridge = CvBridge()

#         # 구독자 생성
#         self.create_subscription(Image, '/camera/camera/color/image_raw', self.image_callback, 10)
#         self.create_subscription(PoseStamped, '/robot_pose_slam', self.pose_callback, 10)
#         self.create_subscription(MapData, '/map_data', self.map_callback, 10)  # MapData 구독

#         # 포즈 임시 저장용 딕셔너리
#         self.pose_data = {}

#     def image_callback(self, msg: Image):
#         timestamp = msg.header.stamp.sec + msg.header.stamp.nanosec * 1e-9
#         filename = os.path.join(self.image_dir, f'{timestamp:.9f}.jpg')

#         cv_image = self.bridge.imgmsg_to_cv2(msg, desired_encoding='bgr8')
#         cv2.imwrite(filename, cv_image)

#         self.get_logger().info(f'Image saved: {filename}')

#         # 포즈가 이미 저장되어 있으면 같이 저장
#         if str(timestamp) in self.pose_data:
#             pose_filename = os.path.join(self.pose_dir, f'{timestamp:.9f}.json')
#             with open(pose_filename, 'w') as f:
#                 json.dump(self.pose_data[str(timestamp)], f, indent=2)
#             self.get_logger().info(f'Pose saved: {pose_filename}')
#             del self.pose_data[str(timestamp)]

#     def pose_callback(self, msg: PoseStamped):
#         timestamp = msg.header.stamp.sec + msg.header.stamp.nanosec * 1e-9
#         pose_dict = {
#             'header': {
#                 'stamp': {
#                     'sec': msg.header.stamp.sec,
#                     'nanosec': msg.header.stamp.nanosec,
#                 },
#                 'frame_id': msg.header.frame_id,
#             },
#             'pose': {
#                 'position': {
#                     'x': msg.pose.position.x,
#                     'y': msg.pose.position.y,
#                     'z': msg.pose.position.z,
#                 },
#                 'orientation': {
#                     'x': msg.pose.orientation.x,
#                     'y': msg.pose.orientation.y,
#                     'z': msg.pose.orientation.z,
#                     'w': msg.pose.orientation.w,
#                 }
#             }
#         }

#         # 이미지보다 먼저 오는 경우 임시 저장
#         self.pose_data[str(timestamp)] = pose_dict

#         # 이미지가 이미 저장되어 있으면 같이 저장
#         image_path = os.path.join(self.image_dir, f'{timestamp:.9f}.jpg')
#         if os.path.exists(image_path):
#             pose_filename = os.path.join(self.pose_dir, f'{timestamp:.9f}.json')
#             with open(pose_filename, 'w') as f:
#                 json.dump(pose_dict, f, indent=2)
#             self.get_logger().info(f'Pose saved: {pose_filename}')
#             del self.pose_data[str(timestamp)]

#     def map_callback(self, msg: MapData):
#         # MapData 메시지 타임스탬프 기준 저장
#         timestamp = msg.header.stamp.sec + msg.header.stamp.nanosec * 1e-9

#         # MapData를 dict로 변환해서 저장
#         map_dict = self.mapdata_to_dict(msg)

#         map_filename = os.path.join(self.map_dir, f'{timestamp:.9f}.json')
#         with open(map_filename, 'w') as f:
#             json.dump(map_dict, f, indent=2)

#         self.get_logger().info(f'MapData saved: {map_filename}')

#     def mapdata_to_dict(self, msg):
#         # 메시지 구조에 맞게 변환, 필요한 필드만 예시로 변환
#         return {
#             'header': {
#                 'stamp': {
#                     'sec': msg.header.stamp.sec,
#                     'nanosec': msg.header.stamp.nanosec,
#                 },
#                 'frame_id': msg.header.frame_id,
#             },
#             'graph': {
#                 'header': {
#                     'stamp': {
#                         'sec': msg.graph.header.stamp.sec,
#                         'nanosec': msg.graph.header.stamp.nanosec,
#                     },
#                     'frame_id': msg.graph.header.frame_id,
#                 },
#                 'poses_id': list(msg.graph.poses_id),
#                 'poses': [
#                     {
#                         'header': {
#                             'stamp': {
#                                 'sec': p.header.stamp.sec,
#                                 'nanosec': p.header.stamp.nanosec,
#                             },
#                             'frame_id': p.header.frame_id,
#                         },
#                         'pose': {
#                             'position': {
#                                 'x': p.pose.position.x,
#                                 'y': p.pose.position.y,
#                                 'z': p.pose.position.z,
#                             },
#                             'orientation': {
#                                 'x': p.pose.orientation.x,
#                                 'y': p.pose.orientation.y,
#                                 'z': p.pose.orientation.z,
#                                 'w': p.pose.orientation.w,
#                             }
#                         }
#                     } for p in msg.graph.poses
#                 ],
#             },
#             'nodes': [
#                 {
#                     'id': n.id,
#                     'word_pts': [
#                         {
#                             'x': pt.x,
#                             'y': pt.y,
#                             'z': pt.z,
#                         } for pt in n.word_pts
#                     ]
#                 } for n in msg.nodes
#             ]
#         }

# def main(args=None):
#     rclpy.init(args=args)
#     node = ImagePoseSaver()
#     rclpy.spin(node)
#     node.destroy_node()
#     rclpy.shutdown()

# if __name__ == '__main__':
#     main()
