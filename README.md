# traversability_code
### recoding_topic.py
ORB-SLAM2에서 이미지와 포즈를 기록하기 위한 코드입니다.

---

### projection.py
포즈를 읽어와 3D transform 후 카메라 좌표로 변환하고, 첫 번째 pose 기준으로 투영합니다.  
투영한 점을 이미지에 표시하고, 변환된 pose 좌표와 함께 이미지 및 데이터를 저장합니다.

---

### segmentation_09_30.py
원본 이미지와 점 좌표를 기반으로 segmentation을 수행합니다.  
마스크(mask)를 이미지에 오버레이한 결과와 마스크 자체를 저장합니다.  

코드에 포함된 주요 기능:  
- 너무 작은 mask는 무시  
- 첫 프레임의 mask는 사용자 선택  
- 후속 프레임은 이전 mask를 고려하여 자동으로 다음 mask를 선택
