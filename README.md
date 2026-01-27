# traversability_code
recoding_topic.py: ORB-SLAM2에서 image, pose를 기록하기 위한 용도의 코드
projection.py: pose 읽어와 -> 3D transform -> 카메라 좌표로 변환 -> 첫 pose 기준 투영
    -> 이미지에 projection한 점을 찍은 이미지, 변환한 pose 좌표가 저장됨
segmentation_09_30.py: 원본 이미지 + 점 좌표 기반으로 segmentation 수행 -> mask를 이미지에 오버레이한 결과, mask 저장
  - 코드에 포함되어 있는 작업들
    -> 너무 작은 mask는 무시
    -> 첫 프레임의 mask는 사용자 선택
    -> 후속 프레임의 mask를 고려해서 다음 mask를 고르도록 하는 것
