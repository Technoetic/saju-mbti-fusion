"""engine.divination.palm — 수상학 도메인 서브패키지 (ADR-039)

이전 평면 → 본 서브폴더 이전 (구→신):
  palm_reading  →  palm.reading
  palm_scoring  →  palm.scoring

ADR-215~228 통합 모듈 (본 세션 신규):
  - line_extraction: Gabor 손금 선 검출 (ADR-215)
  - unet_line_extractor: U-Net 인터페이스 + Gabor fallback (ADR-216·217)
  - unet_model: Ronneberger 표준 아키텍처 (ADR-217·218)
  - train_unet: fine-tune CLI 스크립트 (ADR-221·223)
  - generate_training_data: 합성 학습 데이터 (ADR-223)
  - dataset_pipeline: Roboflow + 사용자 + 합성 + Gemini 4 갈래 (ADR-225)
  - gemini_image_generator: Gemini 2.5 Flash Image API (ADR-228)
  - self_training: pseudo-label 반복 학습 (ADR-226)
  - augmentation: 데이터 증강 (ADR-227)
  - prevalence: 한국 손금 통계 (ADR-192)
"""
