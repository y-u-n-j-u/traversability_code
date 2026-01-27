import json
import cv2
import torch
import numpy as np
import os
import re
from sam2.sam2_image_predictor import SAM2ImagePredictor
from sam2.build_sam import build_sam2 

# --------------------------
# 0. 장치 설정
# --------------------------
device = "cuda" if torch.cuda.is_available() else "cpu"

# --------------------------
# 1. 입력/출력 폴더 설정
# --------------------------
images_dir = "bagfile_result3/output_images_2"
points_dir = "bagfile_result3/output_pixel"
sam_checkpoint = "checkpoints/sam2.1_hiera_large.pt"
model_type = "configs/sam2.1/sam2.1_hiera_l.yaml"

results_dir = "results_final"
masks_dir = os.path.join(results_dir, "masks")
overlays_dir = os.path.join(results_dir, "overlays")
os.makedirs(masks_dir, exist_ok=True)
os.makedirs(overlays_dir, exist_ok=True)

# --------------------------
# 2. SAM 모델 로드
# --------------------------
sam2_model = build_sam2(model_type, sam_checkpoint, device=device)
predictor = SAM2ImagePredictor(sam2_model)

# --------------------------
# 3. IoU 계산 함수
# --------------------------
def compute_iou(mask1, mask2):
    inter = np.logical_and(mask1, mask2).sum()
    union = np.logical_or(mask1, mask2).sum()
    return inter / union if union > 0 else 0.0

# --------------------------
# 4. 색상 팔레트
# --------------------------
colors = [
    (255, 0, 0), (0, 255, 0), (0, 0, 255),
    (255, 255, 0), (255, 0, 255), (0, 255, 255),
    (128, 0, 128), (255, 165, 0),
]
alpha = 0.5

# --------------------------
# 5. 매개변수
# --------------------------
min_area_ratio = 1/9  # 전체 이미지 대비 최소 mask 면적
penalty_ratio = 0.25  # IoU 패널티 비율

# --------------------------
# 6. 이미지 파일 목록
# --------------------------
def numerical_sort(value):
    basename = os.path.splitext(os.path.basename(value))[0]
    numbers = [int(s) for s in basename.split('_') if s.isdigit()]
    return numbers[0] if numbers else -1

image_files = sorted(
    [f for f in os.listdir(images_dir) if f.endswith((".jpg", ".png"))],
    key=numerical_sort
)

# --------------------------
# 7. 초기 설정
# --------------------------
ref_mask = None
first_frame = True

# --------------------------
# 8. 메인 루프
# --------------------------
for img_file in image_files:
    image_path = os.path.join(images_dir, img_file)
    json_path = os.path.join(points_dir, f"{os.path.splitext(img_file)[0]}.json")

    if not os.path.exists(json_path):
        print(f"⚠ JSON 없음 → 건너뜀: {img_file}")
        continue

    # 1. 컬러 이미지 로드
    image_rgb = cv2.imread(image_path, cv2.IMREAD_COLOR)
    if image_rgb is None:
        print(f"⚠ 이미지 로드 실패 → 건너뜀: {img_file}")
        continue
    image_rgb = cv2.cvtColor(image_rgb, cv2.COLOR_BGR2RGB)
    H, W = image_rgb.shape[:2]

    # 2. JSON 좌표 불러오기
    with open(json_path, 'r') as f:
        points_data = json.load(f)
    if len(points_data) == 0:
        print(f"⚠ JSON 점 없음 → 건너뜀: {img_file}")
        continue
    input_points = np.array(points_data, dtype=np.float32)
    if input_points.ndim != 2 or input_points.shape[1] != 2:
        print(f"⚠ JSON 포인트 오류 → 건너뜀: {json_path}")
        continue
    input_labels = np.ones(len(input_points), dtype=np.int32)

    # 3. SAM2 예측
    predictor.set_image(image_rgb)
    masks, scores, logits = predictor.predict(
        point_coords=input_points,
        point_labels=input_labels,
        multimask_output=True
    )
    if masks is None or len(masks) == 0:
        print(f"⚠ 마스크 없음 → 건너뜀: {img_file}")
        continue

    # 4. 첫 프레임 → 수동 선택
    if first_frame:
        print(f"📌 첫 프레임: {img_file}, 후보 {len(masks)}개 저장 중...")
        for i, mask in enumerate(masks):
            overlay = image_rgb.copy()
            mask_bool = mask.astype(bool)
            mask_color = np.zeros_like(overlay)
            mask_color[:, :, :] = (0, 255, 0)
            overlay[mask_bool] = cv2.addWeighted(overlay, 0.5, mask_color, 0.5, 0)[mask_bool]
            save_path = os.path.join(overlays_dir, f"{os.path.splitext(img_file)[0]}_candidate{i}.png")
            cv2.imwrite(save_path, cv2.cvtColor(overlay, cv2.COLOR_RGB2BGR))
        chosen_idx = int(input(f"👉 원하는 마스크 번호 입력 (0 ~ {len(masks)-1}): "))
        ref_mask = masks[chosen_idx]
        first_frame = False
        print(f"✅ 선택된 마스크: {chosen_idx}")
    else:
        # 5. 후속 프레임 → IoU + 패널티 기반 자동 선택
        best_score = -1
        best_mask = None
        for mask in masks:
            mask_bool = mask.astype(bool)
            iou = compute_iou(ref_mask.astype(bool), mask_bool)
            outside_ratio = (mask_bool & (~ref_mask.astype(bool))).sum() / mask_bool.sum()
            score = iou - penalty_ratio * outside_ratio  # 패널티 적용
            if score > best_score:
                best_score = score
                best_mask = mask
        # 면적이 충분하면 ref_mask 갱신
        if best_mask.sum() / (H*W) >= min_area_ratio:
            ref_mask = best_mask
        else:
            print(f"⚠ 선택된 mask 면적 작음 → ref_mask 갱신하지 않음")
        print(f"➡ {img_file} 자동 선택됨, 점수 {best_score:.3f}")

    # 6. 최종 마스크 저장
    mask_img = (ref_mask * 255).astype(np.uint8)
    mask_save_path = os.path.join(masks_dir, f"{os.path.splitext(img_file)[0]}_final.png")
    cv2.imwrite(mask_save_path, mask_img)

    overlay = image_rgb.copy()
    mask_bool = ref_mask.astype(bool)
    mask_color = np.zeros_like(overlay)
    mask_color[:, :, 2] = 255
    overlay[mask_bool] = cv2.addWeighted(overlay, 0.5, mask_color, 0.5, 0)[mask_bool]
    overlay_save_path = os.path.join(overlays_dir, f"{os.path.splitext(img_file)[0]}_final_overlay.png")
    cv2.imwrite(overlay_save_path, cv2.cvtColor(overlay, cv2.COLOR_RGB2BGR))

    print(f"💾 저장 완료: {mask_save_path}, {overlay_save_path}")
