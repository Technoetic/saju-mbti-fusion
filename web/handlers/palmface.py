"""웹 API 핸들러 — palmface 도메인 (구조 리팩터링 2026-06-21).

PersonalityAPIServer 가 본 Mixin 을 상속. self.engine·self.saju_cli·self._analytics 등
공유 상태는 최종 클래스에서 제공되므로 본 파일에서 정의하지 않는다.
원본 web/server.py 에서 메서드 블록을 물리적으로 분리 (동작 불변).
"""
from __future__ import annotations

import asyncio  # noqa: F401
from pathlib import Path  # noqa: F401
from typing import Any  # noqa: F401

from fastapi import HTTPException, Request  # noqa: F401
from fastapi.responses import StreamingResponse  # noqa: F401

import web.schemas as _schemas
from web.schemas import *  # noqa: F401,F403


class PalmFaceHandlersMixin:
    """palmface 도메인 핸들러 묶음 (Mixin)."""

    async def post_face_reading(
        self, req: FaceReadingRequest
    ) -> dict[str, Any]:
        """운학 도사 얼굴 풀이 — Gemini Vision 멀티모달 호출 + 캐시.

        ADR-035 (Phase 3회차): 5MB 초과 시 HTTP 413 명확 오류 반환.
        base64 길이 사전 검사 (7MB ≈ 5MB 바이너리) → 조기 차단.
        """
        # 서버측 이미지 크기 안전망 — 5MB 바이너리 ≈ base64 7MB
        _MAX_B64_LEN = 7 * 1024 * 1024  # 7_340_032 chars
        raw_b64 = req.image_base64 or ""
        # data URL prefix 제거 후 길이 체크
        b64_body = raw_b64.split(",", 1)[-1] if "," in raw_b64 else raw_b64
        if len(b64_body) > _MAX_B64_LEN:
            raise HTTPException(
                status_code=413,
                detail="이미지가 너무 큽니다 — 5MB 이하 JPG/PNG/WEBP로 변환 후 업로드해주세요.",
            )

        try:
            from engine.divination.face.reading import generate_face_reading

            # ADR-274 — 학파 선택 메타를 metrics에 주입 (face/reading.py 시스템 프롬프트 분기)
            _metrics_with_school = dict(req.metrics or {}) if req.metrics else {}
            if req.school:
                _metrics_with_school["physiognomy_school"] = req.school
            result = await asyncio.to_thread(
                generate_face_reading,
                req.image_base64,
                req.age,
                req.gender,
                req.question,
                _metrics_with_school if _metrics_with_school else None,
            )

            # ADR-273 — 관상 12궁 + 5악 시각화 오버레이
            try:
                face_keypoints = None
                if req.metrics and isinstance(req.metrics, dict):
                    face_keypoints = req.metrics.get("face_keypoints")
                if face_keypoints and req.image_base64:
                    from engine.divination.face.visualization import overlay_face_analysis
                    from PIL import Image as _PILImg
                    from io import BytesIO as _BIO
                    import base64 as _b64m
                    import numpy as _npm
                    _s = req.image_base64
                    if "," in _s and _s.startswith("data:"):
                        _s = _s.split(",", 1)[1]
                    img_bytes = _b64m.b64decode(_s)
                    pil_img = _PILImg.open(_BIO(img_bytes)).convert("RGB")
                    img_arr = _npm.asarray(pil_img)
                    fviz = await asyncio.to_thread(
                        overlay_face_analysis,
                        img_arr, face_keypoints, None, True, True, False,
                    )
                    if isinstance(result, dict):
                        result["visualization"] = {
                            "image_base64": fviz.image_base64,
                            "width": fviz.width,
                            "height": fviz.height,
                            "n_palaces_drawn": fviz.n_palaces_drawn,
                            "metadata": fviz.metadata,
                        }
            except Exception:
                pass

            # ADR-006/094 단정 어휘 + ADR-115 다국어 hallucination 사후 필터링
            # (face Vision API 직접 호출 경로 — content/reading 분기 우회)
            if isinstance(result, dict) and "text" in result:
                result["text"] = _sanitize_common_assertion_words(result["text"])
                result["text"] = _sanitize_foreign_hallucination(result["text"])
                result["text"] = _sanitize_korean_grammar_dupes(result["text"])
            # LLM 출력 운영 모니터링 — 1% 샘플링, 사용자 영향 0
            try:
                from engine.safety.llm.output_sampler import sample_llm_output
                sample_llm_output("face_reading", result.get("text", ""))
            except Exception:
                pass  # silent
            return result
        except ValueError as ve:
            raise HTTPException(400, str(ve))
        except Exception as e:
            raise HTTPException(500, str(e))

    async def get_palm_diagnostics(self) -> dict[str, Any]:
        """ADR-242 — 손금 U-Net/CFM 가중치 활성화 진단 (라이브 검증용).

        반환: PyTorch 가용·가중치 경로·파일 크기·모델 유형(CFM/UNet)·상태.
        Vision LLM 호출 없이 가벼움.
        """
        try:
            import os as _os
            from engine.divination.palm.unet_line_extractor import check_unet_availability
            avail = check_unet_availability()
            weights_size = None
            model_type = "unknown"
            state_keys_sample: list[str] = []
            if avail.model_weights_path and _os.path.exists(avail.model_weights_path):
                weights_size = _os.path.getsize(avail.model_weights_path)
                # ADR-253 — .onnx 경로면 ONNX 메타 추출, 아니면 .pt state_dict
                if avail.model_weights_path.endswith(".onnx"):
                    try:
                        import onnx as _onnx
                        m = _onnx.load(avail.model_weights_path)
                        names = [init.name for init in m.graph.initializer]
                        state_keys_sample = names[:6]
                        is_cfm = any(
                            "cfm" in k or "branch" in k
                            or ("attention" in k and "psi" in k)
                            for k in names
                        )
                        model_type = "cfm-onnx" if is_cfm else "unet-onnx"
                    except Exception as e:
                        model_type = f"onnx_meta_error: {type(e).__name__}"
                elif avail.pytorch_available:
                    try:
                        import torch as _torch
                        state = _torch.load(
                            avail.model_weights_path,
                            map_location="cpu",
                            weights_only=True,
                        )
                        if isinstance(state, dict) and "state_dict" in state:
                            state = state["state_dict"]
                        if isinstance(state, dict):
                            keys = list(state.keys())
                            state_keys_sample = keys[:6]
                            is_cfm = any(
                                "cfm" in k or "branch" in k
                                or ("attention" in k and "psi" in k)
                                for k in keys
                            )
                            model_type = "cfm" if is_cfm else "unet"
                    except Exception as e:
                        model_type = f"load_error: {type(e).__name__}"
            return {
                "pytorch_available": avail.pytorch_available,
                "model_weights_path": avail.model_weights_path,
                "model_loadable": avail.model_loadable,
                "fallback_reason": avail.fallback_reason,
                "weights_size_bytes": weights_size,
                "model_type": model_type,
                "state_keys_sample": state_keys_sample,
            }
        except Exception as e:
            return {"error": str(e), "type": type(e).__name__}

    async def post_palm_reading(
        self, req: PalmReadingRequest
    ) -> dict[str, Any]:
        """옥선 할미 손금 풀이 — Vision 멀티모달 + ADR-160 MediaPipe 결정론 점수."""
        try:
            from engine.divination.palm.reading import generate_palm_reading

            # ADR-160 — MediaPipe Hand 21 keypoint 입력 시 결정론 점수 산출.
            # 산출 실패·keypoint 부재 시 LLM Vision 단독 유지 (무회귀).
            palm_deterministic_block = None
            palm_visualization = None  # ADR-259 시각화 오버레이

            # ADR-261 — keypoints 부재 시도 CFM 마스크 단독 시각화 (마스크 + 영역 박스만).
            # MediaPipe 추출 실패한 사용자도 모델 검출 결과 시각 확인 가능.
            if (palm_visualization is None
                    and req.image_base64
                    and not (req.metrics and isinstance(req.metrics, dict)
                             and isinstance(req.metrics.get("keypoints"), dict)
                             and any(k.startswith("kp") for k in req.metrics.get("keypoints", {})))):
                try:
                    from PIL import Image as _PILImg
                    from io import BytesIO as _BIO
                    import base64 as _b64_mod
                    import numpy as _np_mod
                    # ADR-261 fix — data URL prefix ("data:image/jpeg;base64,") 제거
                    _img_str = req.image_base64
                    if "," in _img_str and _img_str.startswith("data:"):
                        _img_str = _img_str.split(",", 1)[1]
                    img_bytes = _b64_mod.b64decode(_img_str)
                    pil_img = _PILImg.open(_BIO(img_bytes)).convert("RGB")
                    img_array_solo = _np_mod.asarray(pil_img)

                    from engine.divination.palm.unet_line_extractor import (
                        extract_palm_lines_best_available,
                    )
                    from engine.divination.palm.visualization import overlay_palm_analysis
                    cfm_r = await asyncio.to_thread(
                        extract_palm_lines_best_available, img_array_solo,
                    )
                    if cfm_r and cfm_r.used_unet and cfm_r.mask is not None:
                        # ADR-271 — keypoint 부재 시 곱선/라벨 미표시.
                        # 표준 비율로 그린 곱선이 손 위치와 무관해 잘못된 시각화 차단.
                        # CFM 마스크만 보여줘 모델 검출 결과만 표시.
                        viz_solo = await asyncio.to_thread(
                            overlay_palm_analysis,
                            img_array_solo, None, cfm_r.mask, None, cfm_r.raw_metrics,
                            0.4, False, True, False,  # show_keypoints=False, show_mask=True, show_regions=False
                        )
                        palm_visualization = {
                            "image_base64": viz_solo.image_base64,
                            "width": viz_solo.width,
                            "height": viz_solo.height,
                            "n_keypoints": 0,
                            "has_cfm_mask": viz_solo.has_cfm_mask,
                            "metadata": viz_solo.metadata,
                            "keypoint_mode": "absent",
                        }
                except Exception:
                    pass

            if req.metrics and isinstance(req.metrics, dict):
                keypoints = req.metrics.get("keypoints")
                if isinstance(keypoints, dict) and any(k.startswith("kp") for k in keypoints):
                    try:
                        # ADR-250 — score_palm_with_cfm: keypoint + CFM 마스크 결합.
                        # image 디코드 성공 시 CFM 가중 결합, 실패 시 keypoint-only fallback.
                        from engine.divination.palm.scoring import score_palm_with_cfm
                        hand_side = req.hand or req.metrics.get("hand_side_mp") or "unknown"

                        # base64 → numpy (PIL 사용, 가벼움)
                        img_array = None
                        if req.image_base64:
                            try:
                                from PIL import Image
                                from io import BytesIO
                                import base64 as _b64
                                import numpy as _np
                                # ADR-261 fix — data URL prefix 제거
                                _b64_str = req.image_base64
                                if "," in _b64_str and _b64_str.startswith("data:"):
                                    _b64_str = _b64_str.split(",", 1)[1]
                                img_bytes = _b64.b64decode(_b64_str)
                                pil_img = Image.open(BytesIO(img_bytes)).convert("RGB")
                                img_array = _np.asarray(pil_img)
                            except Exception:
                                img_array = None

                        palm_report = await asyncio.to_thread(
                            score_palm_with_cfm, keypoints, img_array, hand_side,
                        )
                        # 결정론 점수 메타를 system prompt 주입용 블록으로 압축.
                        lines_summary = " · ".join(
                            f"{ls.name}({ls.label_ko or ls.label}/{ls.score:.2f})"
                            for ls in palm_report.lines.values()
                        )
                        cfm_used = palm_report.metadata.get("cfm_used", False)
                        adr_tag = "ADR-250 CFM 융합" if cfm_used else "ADR-160 keypoint only"
                        palm_deterministic_block = (
                            f"[손금 결정론 — {adr_tag}]\n"
                            f"  · 손 측: {palm_report.hand_side}\n"
                            f"  · 4 손금선 + 금성대 점수: {lines_summary}\n"
                            f"  · CFM 마스크 결합: {'YES (UNetCFM, F1 0.86 baseline)' if cfm_used else 'NO (image 부재 또는 모델 미가용)'}\n"
                            f"[안전 장치 — ADR-006/113] 결정론 점수만 인용. "
                            f"수명·재물·운명 단정 금지. 형태 분류 메타로만 풀이.\n"
                            f"{palm_report.disclaimer_ko}"
                        )

                        # ADR-259 — 손금 시각화 오버레이 생성 (img_array + cfm 가용 시).
                        if cfm_used and img_array is not None:
                            try:
                                from engine.divination.palm.visualization import (
                                    overlay_palm_analysis,
                                )
                                from engine.divination.palm.unet_line_extractor import (
                                    extract_palm_lines_best_available,
                                )
                                # CFM 재추론 (마스크 시각화에 필요 — palm_report에는 마스크 X)
                                cfm_viz_result = await asyncio.to_thread(
                                    extract_palm_lines_best_available, img_array,
                                )
                                line_scores_dict = {
                                    k: float(ls.score)
                                    for k, ls in palm_report.lines.items()
                                }
                                viz = await asyncio.to_thread(
                                    overlay_palm_analysis,
                                    img_array, keypoints,
                                    cfm_viz_result.mask if cfm_viz_result else None,
                                    line_scores_dict,
                                    palm_report.metadata.get("cfm_raw_metrics"),
                                )
                                palm_visualization = {
                                    "image_base64": viz.image_base64,
                                    "width": viz.width,
                                    "height": viz.height,
                                    "n_keypoints": viz.n_keypoints,
                                    "has_cfm_mask": viz.has_cfm_mask,
                                    "metadata": viz.metadata,
                                }
                            except Exception:
                                palm_visualization = None
                    except Exception:
                        pass

            # ADR-256 — LLM 실패 시 결정론 점수 + 친절 안내 반환 (502 회피).
            try:
                result = await asyncio.to_thread(
                    generate_palm_reading,
                    req.image_base64,
                    req.age,
                    req.gender,
                    req.hand,
                    req.question,
                )
            except Exception as llm_err:
                # Vision LLM 실패 → 결정론 점수 + 옥선 할미 어조 안내
                fallback_text = (
                    "허허, 오늘은 이 할미의 눈이 조금 흐려져 손금이 자세히 안 보이는구만. "
                    "잠시 후 다시 손을 펼쳐 보여주시게.\n\n"
                )
                if palm_deterministic_block:
                    fallback_text += (
                        "다만 결정론 분석은 잠시 살펴봤네:\n"
                        + palm_deterministic_block.split("\n", 1)[1].split("[안전")[0]
                    )
                fallback_text += (
                    "\n\n※ 본 결과는 참고용이며, 의료·법률·금융 의사결정의 단독 근거가 될 수 없습니다."
                )
                result = {
                    "text": fallback_text,
                    "cached": False,
                    "llm_fallback": True,
                    "llm_error": type(llm_err).__name__,
                }
            # 결정론 블록을 result에 노출 (LLM 호출자 inject 가능).
            if palm_deterministic_block and isinstance(result, dict):
                result["deterministic_block"] = palm_deterministic_block
            # ADR-259 — 시각화 오버레이 추가
            if palm_visualization and isinstance(result, dict):
                result["visualization"] = palm_visualization
            # ADR-006/094/113 단정 어휘 + ADR-115 다국어 hallucination 사후 필터링
            if isinstance(result, dict) and "text" in result:
                result["text"] = _sanitize_common_assertion_words(result["text"])
                result["text"] = _sanitize_foreign_hallucination(result["text"])
                result["text"] = _sanitize_korean_grammar_dupes(result["text"])
            return result
        except ValueError as ve:
            raise HTTPException(400, str(ve))
        except Exception as e:
            # ADR-256 최후 fallback — 그래도 502 안 내고 친절 메시지
            return {
                "text": "허허, 잠시 후 다시 시도해주시게. 이 할미의 눈이 흐려져 있어. "
                        "※ 참고용이며 의료·법률·금융 의사결정의 단독 근거가 될 수 없습니다.",
                "cached": False,
                "fatal_error": type(e).__name__,
            }
