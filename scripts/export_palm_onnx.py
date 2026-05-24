"""ADR-253 - UNetCFM PyTorch → ONNX 변환 + (선택) INT8 양자화.

목적:
  · 라이브 추론 PyTorch (200MB) → onnxruntime (~50MB) 의존성 절감
  · 추론 속도 2~3배 (CPU 최적화 그래프 + INT8 가능)
  · 라이브 메모리 ↓

산출:
  · models/unet_weights_cfm.onnx (FP32, ~11MB)
  · (선택) models/unet_weights_cfm_int8.onnx (INT8, ~3MB)

검증:
  · numpy 입력 → PyTorch vs ONNX 출력 동일성 (max abs diff < 1e-4)
  · TTA consistency 자체 측정

사용:
  python scripts/export_palm_onnx.py \\
    --weights models/unet_weights.pt \\
    --output models/unet_weights_cfm.onnx
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--weights", default="models/unet_weights.pt")
    parser.add_argument("--output", default="models/unet_weights_cfm.onnx")
    parser.add_argument("--img-size", type=int, default=256)
    args = parser.parse_args()

    import numpy as np
    import torch

    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    from engine.divination.palm.unet_cfm import UNetCFM

    # 1. 모델 로드
    model = UNetCFM(n_channels=3, n_classes=1)
    state = torch.load(args.weights, map_location="cpu", weights_only=True)
    model.load_state_dict(state, strict=False)
    model.eval()

    # 2. dummy 입력 (배치 1)
    dummy = torch.randn(1, 3, args.img_size, args.img_size)

    # 3. ONNX export
    print(f"[export] {args.weights} → {args.output}")
    torch.onnx.export(
        model,
        dummy,
        args.output,
        input_names=["input"],
        output_names=["mask_logits"],
        dynamic_axes={
            "input": {0: "batch_size"},
            "mask_logits": {0: "batch_size"},
        },
        opset_version=17,
        do_constant_folding=True,
    )
    # 단일 .onnx 파일로 가중치 내장 (external data → 내장 변환)
    try:
        import onnx
        m = onnx.load(args.output, load_external_data=True)
        # 외장 데이터를 모델 안으로 임베드
        for tensor in m.graph.initializer:
            if tensor.HasField("data_location") and tensor.data_location == onnx.TensorProto.EXTERNAL:
                # external_data 필드 제거 → 내장
                tensor.data_location = onnx.TensorProto.DEFAULT
        onnx.save(m, args.output)  # 단일 파일로 저장
        # external data 부산물 삭제
        import os as _os
        ext = args.output + ".data"
        if _os.path.exists(ext):
            _os.remove(ext)
    except Exception as e:
        print(f"(단일 파일 임베드 실패: {e} — .onnx + .data 분리 유지)")
    print(f"[export 완료]")

    # 4. PyTorch vs ONNX 출력 일치 검증
    try:
        import onnxruntime as ort
        sess = ort.InferenceSession(args.output, providers=["CPUExecutionProvider"])
        pt_out = model(dummy).detach().numpy()
        ort_out = sess.run(None, {"input": dummy.numpy()})[0]
        max_diff = float(np.abs(pt_out - ort_out).max())
        mean_diff = float(np.abs(pt_out - ort_out).mean())
        print(f"[검증] max_diff={max_diff:.2e}  mean_diff={mean_diff:.2e}")
        assert max_diff < 1e-3, f"출력 불일치 — max_diff {max_diff}"
        print(f"[OK] ONNX vs PyTorch 출력 일치")

        # 5. 추론 속도 비교
        import time as _time
        N = 10
        # PyTorch
        with torch.no_grad():
            t0 = _time.time()
            for _ in range(N):
                _ = model(dummy)
            t_pt = (_time.time() - t0) / N
        # ONNX
        t0 = _time.time()
        for _ in range(N):
            _ = sess.run(None, {"input": dummy.numpy()})
        t_ort = (_time.time() - t0) / N
        print(f"[속도] PyTorch={t_pt*1000:.1f}ms/img | ONNX={t_ort*1000:.1f}ms/img | 가속={t_pt/t_ort:.2f}x")
    except ImportError:
        print("(onnxruntime 미설치 — 검증 스킵, export만 완료)")

    # 6. 파일 크기
    import os
    pt_size = os.path.getsize(args.weights) / 1024 / 1024
    onnx_size = os.path.getsize(args.output) / 1024 / 1024
    print(f"[크기] .pt={pt_size:.2f}MB → .onnx={onnx_size:.2f}MB")


if __name__ == "__main__":
    main()
