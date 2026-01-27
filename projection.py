# import glob
# import numpy as np
# import json
# import cv2
# import os
# from scipy.spatial.transform import Rotation as R

# pose_file_paths = sorted(glob.glob("data/poses/*.json"))

# base_step = 1    # 기준 이미지 건너뛰기 간격 (10씩)
# window_size = 4
# step = 10         # 점 찍는 이미지 간격 (15씩)

# fx = 637.3329467773438
# fy = 636.649047851562
# cx = 629.9596557617188
# cy = 373.2369079589844
# K = np.array([[fx, 0, cx],[0, fy, cy],[0, 0, 1]])
# H = 55.0

# output_dir_image = "output_images_2"
# os.makedirs(output_dir_image, exist_ok=True)
# output_dir_pixel = "output_pixel_2"
# os.makedirs(output_dir_pixel, exist_ok=True)

# def pose_to_transform(position, orientation):
#     r = R.from_quat([orientation['x'], orientation['y'], orientation['z'], orientation['w']])
#     R_mat = r.as_matrix()
#     R_cam_to_robot = np.array([[0,0,1],[-1,0,0],[0,-1,0]])
#     R_mat_corrected = R_mat @ R_cam_to_robot
#     t = np.array([position['x'], position['y'], position['z']]).reshape(3,1)
#     T = np.eye(4)
#     T[:3,:3] = R_mat_corrected
#     T[:3,3:] = t
#     return T

# def invert_transform(T):
#     R_mat = T[:3,:3]
#     t = T[:3,3]
#     R_inv = R_mat.T
#     t_inv = -R_inv @ t
#     T_inv = np.eye(4)
#     T_inv[:3,:3] = R_inv
#     T_inv[:3,3] = t_inv
#     return T_inv

# def project_points(points_W, T_CW, K):
#     N = points_W.shape[0]
#     points_W = points_W[1:]
#     homo_points = np.hstack([points_W, np.ones((N-1,1))]).T
#     points_C = T_CW @ homo_points
#     points_C = points_C[:3,:]
#     u = (K @ points_C)[0,:] / points_C[2,:]
#     v = (K @ points_C)[1,:] / points_C[2,:]
#     pixels = np.vstack([u,v]).T
#     return pixels

# for start_idx in range(0, len(pose_file_paths), base_step):
#     indices = [start_idx + step * i for i in range(window_size)]
#     valid_indices = [i for i in indices if i < len(pose_file_paths)]
#     batch_files = [pose_file_paths[i] for i in valid_indices]

#     print(f"Processing batch starting at {start_idx}, files: {batch_files}")

#     positions = []
#     orientations = []
#     for fpath in batch_files:
#         with open(fpath, 'r') as f:
#             data = json.load(f)
#         pos = data['pose']['position']
#         ori = data['pose']['orientation']
#         positions.append([pos['x'], pos['y'], pos['z']])
#         orientations.append(ori)
#     positions = np.array(positions)

#     footsteps = positions.copy()
#     footsteps[1:, 2] -= H

#     T_CWs = []
#     for pos, ori in zip(positions, orientations):
#         T_WC = pose_to_transform({'x': pos[0], 'y': pos[1], 'z': pos[2]}, ori)
#         T_CW = invert_transform(T_WC)
#         T_CWs.append(T_CW)

#     pixels = project_points(footsteps, T_CWs[0], K)

#     ref_pose_file = batch_files[0]
#     timestamp = os.path.splitext(os.path.basename(ref_pose_file))[0]
#     image_path = f"data/images/{timestamp}.jpg"

#     img = cv2.imread(image_path)
#     if img is None:
#         print(f"이미지를 찾을 수 없습니다: {image_path}")
#         continue

#     # y 좌표가 250 이상인 점만 필터링
#     filtered_pixels = [ [u, v] for u, v in pixels if v >= 250 ]

#     # for (u,v) in filtered_pixels:
#     #     cv2.circle(img, (int(u), int(v)), radius=5, color=(0,0,255), thickness=-1)

#     save_path = os.path.join(output_dir_image, f"projected_footsteps_batch_{start_idx}.png")
#     cv2.imwrite(save_path, img)
#     print(f"이미지를 저장했습니다: {save_path}")

#     json_save_path = os.path.join(output_dir_pixel, f"projected_footsteps_batch_{start_idx}.json")
#     pixel_list = pixels.tolist()
#     with open(json_save_path, 'w') as jf:
#         json.dump(pixel_list, jf, indent=2)
#     print(f"픽셀 좌표 JSON 파일을 저장했습니다: {json_save_path}")

import glob
import numpy as np
import json
import cv2
import os
from scipy.spatial.transform import Rotation as R

# pose 파일 경로
pose_file_paths = sorted(glob.glob("data/poses/*.json"))

# 배치 내 pose 선택 기준 인덱스
relative_indices = [0, 5, 15, 30]

# 카메라 내부 파라미터
fx = 637.3329467773438
fy = 636.649047851562
cx = 629.9596557617188
cy = 373.2369079589844
K = np.array([[fx, 0, cx],
              [0, fy, cy],
              [0, 0, 1]])
H = 55.0

# 출력 폴더
output_dir_image = "output_images_2"
os.makedirs(output_dir_image, exist_ok=True)
output_dir_pixel = "output_pixel_2"
os.makedirs(output_dir_pixel, exist_ok=True)

# -------------------------
# 변환 관련 함수
# -------------------------
def pose_to_transform(position, orientation):
    r = R.from_quat([orientation['x'], orientation['y'], orientation['z'], orientation['w']])
    R_mat = r.as_matrix()
    R_cam_to_robot = np.array([[0,0,1],[-1,0,0],[0,-1,0]])
    R_mat_corrected = R_mat @ R_cam_to_robot
    t = np.array([position['x'], position['y'], position['z']]).reshape(3,1)
    T = np.eye(4)
    T[:3,:3] = R_mat_corrected
    T[:3,3:] = t
    return T

def invert_transform(T):
    R_mat = T[:3,:3]
    t = T[:3,3]
    R_inv = R_mat.T
    t_inv = -R_inv @ t
    T_inv = np.eye(4)
    T_inv[:3,:3] = R_inv
    T_inv[:3,3] = t_inv
    return T_inv

def project_points(points_W, T_CW, K):
    N = points_W.shape[0]
    points_W = points_W[1:]
    homo_points = np.hstack([points_W, np.ones((N-1,1))]).T
    points_C = T_CW @ homo_points
    points_C = points_C[:3,:]
    u = (K @ points_C)[0,:] / points_C[2,:]
    v = (K @ points_C)[1,:] / points_C[2,:]
    pixels = np.vstack([u,v]).T
    return pixels

# -------------------------
# 배치 처리 루프
# -------------------------
for start_idx in range(0, len(pose_file_paths)):
    # 배치 내 pose 인덱스 계산
    indices = [start_idx + ri for ri in relative_indices]
    valid_indices = [i for i in indices if i < len(pose_file_paths)]
    batch_files = [pose_file_paths[i] for i in valid_indices]

    print(f"Processing batch starting at {start_idx}, files: {batch_files}")

    # pose 불러오기
    positions = []
    orientations = []
    for fpath in batch_files:
        with open(fpath, 'r') as f:
            data = json.load(f)
        pos = data['pose']['position']
        ori = data['pose']['orientation']
        positions.append([pos['x'], pos['y'], pos['z']])
        orientations.append(ori)
    positions = np.array(positions)

    # 발자국 z 좌표 조정
    footsteps = positions.copy()
    footsteps[1:, 2] -= H

    # 카메라 변환 행렬
    T_CWs = []
    for pos, ori in zip(positions, orientations):
        T_WC = pose_to_transform({'x': pos[0], 'y': pos[1], 'z': pos[2]}, ori)
        T_CW = invert_transform(T_WC)
        T_CWs.append(T_CW)

    # 첫 pose 기준으로 포인트 투영
    pixels = project_points(footsteps, T_CWs[0], K)

    # 이미지 불러오기
    ref_pose_file = batch_files[0]
    timestamp = os.path.splitext(os.path.basename(ref_pose_file))[0]
    image_path = f"data/images/{timestamp}.jpg"

    img = cv2.imread(image_path)
    if img is None:
        print(f"이미지를 찾을 수 없습니다: {image_path}")
        continue

    # y 좌표가 250 이상인 점만 필터링
    filtered_pixels = [ [u, v] for u, v in pixels if v >= 250 ]

    # 점 그리기 (원하면 주석 해제)
    # for (u,v) in filtered_pixels:
    #     cv2.circle(img, (int(u), int(v)), radius=5, color=(0,0,255), thickness=-1)

    # 이미지 저장
    save_path = os.path.join(output_dir_image, f"projected_footsteps_batch_{start_idx}.png")
    cv2.imwrite(save_path, img)
    print(f"이미지를 저장했습니다: {save_path}")

    # 픽셀 좌표 JSON 저장
    json_save_path = os.path.join(output_dir_pixel, f"projected_footsteps_batch_{start_idx}.json")
    pixel_list = pixels.tolist()
    with open(json_save_path, 'w') as jf:
        json.dump(pixel_list, jf, indent=2)
    print(f"픽셀 좌표 JSON 파일을 저장했습니다: {json_save_path}")