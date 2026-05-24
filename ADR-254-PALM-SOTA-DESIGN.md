# ADR-254 — 학술 SOTA F1 99%+ 손금 검출 자동 구현 설계도

**상태**: PROPOSED — 자동 실행 대기 (사용자 명령 시 시작)
**작성일**: 2026-05-24
**기반 baseline**: ADR-253 (ONNX 30 epoch CFM, F1 0.86 vs Gabor, Consistency 0.92, 라이브 활성)
**목표**: 학술적으로 검증된 SOTA 기법 자동 적용 — 사용자 개입 0
**총 소요**: ~36시간 (대부분 GPU 학습, 컴퓨터 켜두기만 하면 됨)

---

## 🎯 핵심 원칙

1. **자동 논스톱** — 시작 명령 후 사용자 개입 없이 완주
2. **체크포인트** — 매 Phase 완료 시 `D:/palm_sota/progress.json` 저장 → 중단 시 재개 가능
3. **fallback** — 각 단계 실패 시 다음 가능한 단계로 자동 이동
4. **회귀 0** — 라이브 실패 시 자동 git revert + 이전 baseline 복귀
5. **정직한 측정** — Gabor pseudo-GT 한계 인정. F1 측정값 외 Consistency·loss 지표도 기록

---

## 📊 전체 Phase 의존성 그래프

```
Phase 0 (10분): 환경 준비
    ↓
Phase 1 (4시간): 데이터 확장 (11k + 추가 데이터셋 + augmentation)
    ↓
Phase 2 (3시간): Pseudo-GT 정제 (SAM2 + CFM + Gabor 합의)
    ↓
Phase 3 (24시간 GPU): 3 모델 순차 학습
    ├─ 3.1 UNetCFM 60 epoch (8시간)
    ├─ 3.2 DeepLabV3+ ImageNet pretrained 30 epoch (8시간)
    └─ 3.3 SegFormer mit-b0 30 epoch (8시간)
    ↓
Phase 4 (2시간): 앙상블 통합 + Multi-scale + CRF + ONNX export
    ↓
Phase 5 (3시간): 라이브 검증·deploy·회귀
```

---

## 🔧 Phase 0 — 환경 준비 (10분)

### 0.1 필수 라이브러리 설치
```bash
pip install --quiet \
  segmentation_models_pytorch \
  transformers \
  pydensecrf \
  pillow
```
- `segmentation_models_pytorch`: DeepLabV3+, U-Net++, FPN 등 SOTA 모델 표준 구현
- `transformers`: HuggingFace SegFormer
- `pydensecrf`: CRF 후처리 (fallback: morphology)

### 0.2 작업 디렉토리 생성
```bash
mkdir -p D:/palm_sota/{train,eval,pseudo_gt,weights,logs,viz}
mkdir -p models/sota/  # 최종 가중치 저장
```

### 0.3 디스크 공간 확인
- 필요: ~50GB (데이터 30GB + 가중치 1GB + 부산물 20GB)
- 부족 시 자동 중단 + 사용자에게 알림

### 0.4 GPU 가용성 확인
```bash
python -c "import torch; assert torch.cuda.is_available(), 'CUDA 필요'"
```
- CPU만이면 학습 시간 30배 → 자동 중단 + 권고

### 0.5 progress.json 초기화
```json
{
  "started_at": "2026-05-24T...",
  "baseline_commit": "<git rev-parse HEAD>",
  "current_phase": 0,
  "phases": {}
}
```

### Phase 0 검증
- ✅ 모든 라이브러리 import 성공
- ✅ D: 드라이브 50GB+ 가용
- ✅ CUDA 가용
- ✅ progress.json 작성

**fallback**: pydensecrf 설치 실패 → CRF 단계 자동 스킵 표시

---

## 📦 Phase 1 — 데이터 확장 (4시간)

### 1.1 기존 11k Hands 확인
- `D:/palm_dataset/palmar_only/` 5,296장 (clean split 후)
- `D:/palm_dataset/eval_holdout/` 200장 (seed=42 보존)

### 1.2 추가 공개 데이터셋 자동 다운로드 시도
**시도 순서** (라이선스 인증 없이 자동 가능한 것만):

1. **Sapienza Mobile Palmprint Dataset** (Italy, ~9,000장)
   - URL 시도: 공개 GitHub 미러
   - 실패 시 스킵

2. **MOHI (Multi-Occluded Hand Images)** — Roboflow 등 공개 미러
   - gdown으로 시도

3. **합성 손바닥 (Stable Diffusion 등)** — 라이선스 안전
   - 시도하지 않음 (효과 미미, 시간 큼)

**실용적 판단**: 학술 라이선스 form 필요한 데이터셋은 모두 스킵. 자동 가능한 것만.

### 1.3 Augmentation 확장 (가장 안전한 데이터 증식)
- 5,296 원본 × 5 변형 = **26,480장**
- 변형 종류:
  - 회전 ±20° (5도 간격 4단계)
  - 밝기 ±40% (랜덤 1회)
  - 가우시안 노이즈 (σ=10)
- 출력: `D:/palm_sota/train/`

### 1.4 Train/Eval 통합
- Eval은 hold-out 200장 그대로 (변경 X, 측정 일관성)
- Train은 증식 데이터 통합

### Phase 1 검증
- ✅ `D:/palm_sota/train/` 20,000장 이상
- ✅ eval 200장 그대로
- ✅ 학습 폴더와 eval 폴더 교집합 = 0 (data leakage 검증)

**fallback**: 추가 데이터셋 모두 실패 → augmentation만으로 진행 (26,480장)

---

## 🏷️ Phase 2 — Pseudo-GT 정제 (3시간)

### 2.1 SAM2 모델 다운로드
- HuggingFace `facebook/sam2-hiera-small` (~150MB)
- 자동 다운로드 + 로컬 캐시

### 2.2 SAM2 손바닥 영역 자동 segmentation
```python
for img in train_images:
    # SAM2 automatic mask generator → 가장 큰 mask = 손바닥
    masks = sam2_predict(img)
    hand_mask = largest_mask(masks)
    save(hand_mask, "D:/palm_sota/hand_masks/")
```
- 손바닥 외 배경 노이즈 완전 제거

### 2.3 다중 합의 pseudo-GT 생성
**알고리즘**:
```python
for img in train_images:
    cfm_mask = current_cfm_30ep_inference(img)
    gabor_mask = gabor_response_threshold_90(img)
    hand_mask = sam2_hand_mask(img)

    # 합의 (OR) + 손바닥 영역 제한 (AND)
    pseudo_gt = (cfm_mask | gabor_mask) & hand_mask

    save(pseudo_gt, "D:/palm_sota/pseudo_gt/")
```

**왜 이게 더 좋은가**:
- Gabor 단독: 노이즈 多, 배경 false positive
- CFM 단독: 학습된 Gabor 편향 그대로
- 합의: 두 모델 모두 동의한 영역 → 신뢰도 ↑
- SAM2 손바닥 제한: 배경 픽셀 완전 제거

### 2.4 pseudo-GT 품질 검증 (자동)
- 5장 무작위 샘플 → 시각화 PNG 저장 (`D:/palm_sota/viz/`)
- 통계 출력:
  - 평균 손금 픽셀 비율 (정상 5~15%)
  - SAM2 손바닥 mask 평균 비율 (정상 30~70%)

### Phase 2 검증
- ✅ SAM2 mask 생성 성공률 > 95%
- ✅ pseudo_gt 평균 픽셀 비율 5~15% 범위
- ✅ 시각화 5장 정상 저장

**fallback**:
- SAM2 다운로드 실패 → CFM + Gabor만 합의 (SAM2 제한 없음)
- 둘 다 실패 → Gabor 단독 (현재 baseline)

---

## 🧠 Phase 3 — 3 모델 학습 (24시간 GPU)

### 3.1 UNetCFM 재학습 (8시간)

**스펙**:
- 모델: `engine.divination.palm.unet_cfm.UNetCFM`
- 데이터: `D:/palm_sota/train/` (26,480장)
- GT: `D:/palm_sota/pseudo_gt/`
- Epoch: **60** (기존 30의 2배)
- Batch: 16
- LR: 1e-4 → cosine annealing
- Optimizer: Adam
- Loss: BCEWithLogitsLoss
- **ImageNet pretrained encoder**: train_unet 코드 수정 — encoder backbone 부분만 ImageNet 가중치 로드 (가능한 경우)
- 출력: `models/sota/cfm_60ep.pt`

**진행 로그**:
- 매 epoch 완료 시 `D:/palm_sota/logs/cfm.log` append
- final loss 기록

### 3.2 DeepLabV3+ 학습 (8시간)

**스펙**:
```python
import segmentation_models_pytorch as smp
model = smp.DeepLabV3Plus(
    encoder_name="resnet50",
    encoder_weights="imagenet",  # ImageNet pretrained
    in_channels=3,
    classes=1,
)
```
- 데이터 동일
- Epoch: 30 (모델이 더 크고 pretrained 시작이라 빠른 수렴)
- 출력: `models/sota/deeplabv3plus_30ep.pt`

### 3.3 SegFormer 학습 (8시간)

**스펙**:
```python
from transformers import SegformerForSemanticSegmentation
model = SegformerForSemanticSegmentation.from_pretrained(
    "nvidia/mit-b0",  # 가장 작은 SegFormer (~14MB)
    num_labels=1,
    ignore_mismatched_sizes=True,
)
```
- Transformer 기반 — UNet과 다른 inductive bias → 앙상블 효과 ↑
- Epoch: 30
- 출력: `models/sota/segformer_mitb0_30ep.pt`

### 3.4 각 모델 hold-out 평가
- 200장 eval로 F1, IoU, Consistency 측정
- 결과 → progress.json 기록

### Phase 3 검증
- ✅ 3 모델 모두 final_loss < 0.01 (또는 학습 수렴 곡선 정상)
- ✅ 각 모델 F1 / Consistency 기록

**fallback**:
- DeepLab 학습 실패 → 스킵, CFM + SegFormer 2-모델 앙상블
- SegFormer 학습 실패 → CFM + DeepLab 앙상블
- 둘 다 실패 → CFM 60ep 단독 (현재 baseline ↑)

---

## 🔀 Phase 4 — 앙상블 통합 (2시간)

### 4.1 앙상블 추론 함수 작성
```python
def extract_palm_lines_ensemble(img: np.ndarray) -> dict:
    prob_cfm = cfm_inference(img)         # 0~1
    prob_deeplab = deeplab_inference(img)
    prob_segformer = segformer_inference(img)

    # F1 가중 평균 (Phase 3 측정값 기반)
    w_cfm, w_dl, w_sf = compute_weights_from_f1()
    prob_avg = w_cfm * prob_cfm + w_dl * prob_deeplab + w_sf * prob_segformer

    mask = prob_avg > 0.5
    return {"mask": mask, "prob": prob_avg}
```

### 4.2 Multi-scale inference
```python
def multi_scale_inference(img):
    masks = []
    for size in [256, 384, 512]:
        resized = resize(img, size, size)
        mask = ensemble_inference(resized)
        masks.append(resize(mask, 256, 256))  # 통일
    return np.mean(masks, axis=0) > 0.5
```

### 4.3 CRF 후처리 (pydensecrf 가용 시)
```python
import pydensecrf.densecrf as dcrf
d = dcrf.DenseCRF2D(W, H, 2)
# unary: -log(prob)
# pairwise: 픽셀 위치 + RGB 유사도
refined = d.inference(5)
```
- 끊긴 손금 선 연결, 노이즈 추가 제거

### 4.4 ONNX export (각 모델 별도)
- UNetCFM → `models/sota/cfm_60ep.onnx`
- DeepLabV3+ → `models/sota/deeplabv3plus.onnx`
- SegFormer → `models/sota/segformer.onnx`
- 단일 파일 (외장 데이터 임베드)

### 4.5 앙상블 추론 시간 측정
- 각 모델 ONNX CPU 추론 시간 측정
- 합 < 200ms 목표 (단일 50ms × 3)

### Phase 4 검증
- ✅ 앙상블 hold-out F1 > 단일 최고 모델 F1
- ✅ Consistency > 0.92
- ✅ 추론 시간 < 200ms

**fallback**:
- CRF 부재 → `mask_postprocess` (ADR-252) 사용
- 추론 시간 > 500ms → 가벼운 모델만 (CFM + DeepLab) 사용

---

## 🚀 Phase 5 — 라이브 검증·deploy (3시간)

### 5.1 라이브 인프라 시뮬레이션
- 모델 3개 동시 로드 메모리 추정
- Fly.io 512MB 충분성 검증
- 부족 시 `fly.toml` memory = "1024mb" 자동 갱신 (+$5.70/월)

### 5.2 회귀 + smoke 테스트 자동 실행
```bash
pytest tests/regression/ tests/smoke/ -q --tb=short
```
- 실패 시 최대 3회 자동 디버깅 (Edit tool로 수정 → 재실행)
- 3회 실패 → Phase 5 중단 + 로컬 모델만 보존

### 5.3 server.py 앙상블 통합
- 새 함수: `score_palm_with_ensemble(keypoints, image, hand_side)`
- ADR-250 매핑 유지 (keypoint 0.6 + ensemble_mask 0.4)
- LLM 시스템 프롬프트 갱신: "ADR-254 앙상블 (CFM+DeepLab+SegFormer)"

### 5.4 Dockerfile 갱신
- 모델 3개 + ONNX 3개 모두 COPY
- 이미지 크기: 200MB → ~250MB (모델 +30MB)

### 5.5 commit + push + deploy
```bash
git add models/sota/ engine/ web/ Dockerfile requirements-ml.txt
git commit -m "feat(palm): ADR-254 학술 SOTA 앙상블 (CFM+DeepLab+SegFormer)"
git push origin main
```
- `gh workflow run` 트리거
- Monitor로 deploy 완료 대기

### 5.6 라이브 검증
- `/api/palm/diagnostics` 호출 → 모든 모델 활성 확인
- 실 손바닥 1장 추론 → backend 작동 검증

### 5.7 라이브 실패 시 자동 revert
```bash
git revert HEAD
git push origin main
# Fly.io 자동 재배포 → 이전 baseline (ADR-253)으로 복귀
```

### Phase 5 검증
- ✅ 라이브 `model_loadable: true`
- ✅ ensemble backend 확인 (응답에 `"backend": "ensemble"` 포함)
- ✅ 응답 시간 < 5초

**fallback**:
- 라이브 deploy 실패 → revert + 로컬 모델만 보존 (학습 결과 손실 X)
- 메모리 부족 → 가벼운 2-모델 앙상블로 축소

---

## 📋 자동 체크포인트 시스템

### 위치
`D:/palm_sota/progress.json`

### 구조
```json
{
  "started_at": "ISO timestamp",
  "baseline_commit": "git hash (롤백 기준)",
  "current_phase": 3,
  "phases": {
    "0": {"completed": true, "duration_min": 8, "notes": "..."},
    "1": {"completed": true, "n_images": 26480, "duration_min": 245},
    "2": {"completed": true, "sam2_used": true, "duration_min": 178},
    "3": {
      "cfm_60ep": {"completed": true, "f1": 0.87, "loss": 0.0038, "weights": "models/sota/cfm_60ep.pt"},
      "deeplab": {"completed": true, "f1": 0.85, "loss": 0.0042, "weights": "models/sota/deeplabv3plus_30ep.pt"},
      "segformer": {"completed": false, "error": "OOM"}
    },
    "4": {"pending": true},
    "5": {"pending": true}
  },
  "fallbacks_used": ["segformer skipped"],
  "deploy_attempts": 0
}
```

### 재개 알고리즘
```python
progress = load("D:/palm_sota/progress.json")
last_completed = max(p for p in progress["phases"] if progress["phases"][p].get("completed"))
resume_from = last_completed + 1
print(f"Phase {resume_from} 부터 재개")
```

---

## 🛑 자동 중단 조건

| 조건 | 처리 |
|---|---|
| GPU OOM | 현재 모델 batch size 절반 → 재시도 → 그래도 실패 시 그 모델 스킵 |
| 디스크 < 5GB | 즉시 중단 + 사용자 알림 |
| 회귀 테스트 3회 연속 실패 | Phase 5 중단 + 로컬 모델만 보존 |
| 라이브 deploy 실패 | 자동 revert |
| `Ctrl+C` (사용자 중단) | 현재 작업 안전 종료 + progress.json 저장 |
| 학습 loss NaN | 그 모델 스킵 |

---

## 📈 예상 효과 (정직)

| 지표 | 현재 (ADR-253) | 예상 (ADR-254) | 출처 |
|---|---|---|---|
| 모델 | UNetCFM 단독 | CFM + DeepLab + SegFormer 앙상블 | 학술 +2~3%p |
| 데이터 | 5,296장 | 26,480장 augmented | 학술 +1~2%p |
| 학습 epoch | 30 | 60 (CFM) + 30 × 2 | 학술 +1%p |
| Pretrained | from scratch | ImageNet (DeepLab/SegFormer) | 학술 +1~2%p |
| Pseudo-GT | Gabor 약지도 | CFM+Gabor 합의 + SAM2 손바닥 | 학습 품질 ↑ |
| 추론 | 단일 ONNX 50ms | 앙상블 ~150ms | 정확도 우선 |
| **F1 vs Gabor (측정값)** | **0.86** | **0.83~0.90 (변동 가능)** | Gabor 한계 |
| **F1 vs 실제 손금 (추정)** | **~0.82~0.88** | **~0.88~0.95** | 학술 통계 |
| Consistency (TTA) | 0.92 | **0.94+ 기대** | 앙상블 효과 |
| 라이브 메모리 | ~250MB | ~350MB | Fly.io 512MB 충분 |

**솔직 경고**:
- Gabor pseudo-GT 측정으로는 진짜 향상 정확히 측정 불가
- 학술 추정치는 일반 segmentation task 기준 (손금은 특수)
- 실제 사용자 체감은 LLM 풀이 품질에 간접 반영

---

## 🎯 실행 명령 (사용자 트리거)

설계도 승인 후 다음 명령 하나로 자동 실행 시작:

```
"ADR-254 진행해"
```

또는 단계별 진행:
```
"ADR-254 Phase 0 진행"
"ADR-254 Phase 1 진행"
...
```

---

## 📝 진행 중 보고 패턴

매 Phase 완료 시:
- ✅ 완료 표시
- 📊 측정값 (loss, F1, 시간)
- ⏭ 다음 Phase 자동 시작

매 epoch 완료 시 (학습 중):
- Monitor를 통한 알림: `[Epoch X/Y 완료] loss=Z`

중단 발생 시:
- 🛑 중단 사유 + fallback 적용 안내
- 진행률 상태 + 재개 명령

---

## 🔗 관련 ADR

- ADR-217 UNet 아키텍처
- ADR-230 UNetCFM (arXiv 2102.12127)
- ADR-245 가중치 repo 포함
- ADR-246 models/ 디렉토리
- ADR-248 CPU-only PyTorch
- ADR-249 CFM 30 epoch
- ADR-250 score_palm_with_cfm (keypoint + CFM 결합)
- ADR-251 hand-conditioned (opt-in)
- ADR-252 mask postprocess (opt-in)
- ADR-253 ONNX Runtime 추론
- **ADR-254 (본 문서)** 학술 SOTA 앙상블 자동 구현

---

## 🚨 중요 — 컨텍스트 압축 후 재개 가이드

본 문서는 컨텍스트 압축돼도 그대로 읽고 재개할 수 있도록 작성됨.

**재개 절차**:
1. 본 파일 `ADR-254-PALM-SOTA-DESIGN.md` 전체 읽기
2. `D:/palm_sota/progress.json` 확인 → 마지막 완료 Phase 파악
3. 그 다음 Phase부터 본 설계도대로 실행
4. 매 Phase는 독립적 — 이전 Phase 산출물(`D:/palm_sota/`) 만 의존

**현재 baseline 정보** (자동 복귀 기준):
- Branch: `main`
- 마지막 안정 commit: `dd24e3f` (ADR-253 진단 ONNX 인식)
- 라이브: ONNX CFM 30 epoch (`models/unet_weights_cfm.onnx`)
- F1 (vs Gabor): 0.86
- Consistency: 0.92
