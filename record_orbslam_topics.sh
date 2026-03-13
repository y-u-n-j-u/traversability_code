#!/bin/bash

# 현재 날짜/시간 생성
DATE=$(date +"%Y%m%d_%H%M%S")

# 저장 폴더
SAVE_DIR=~/rosbags

mkdir -p $SAVE_DIR

# bag 이름
BAG_NAME=$SAVE_DIR/orbslam_${DATE}

echo "Recording bag to: $BAG_NAME"

ros2 bag record \
/camera/camera/color/image_raw \
/camera/camera/depth/image_rect_raw \
/camera/camera/color/camera_info \
/camera/camera/depth/camera_info \
/tf_static \
-o $BAG_NAME