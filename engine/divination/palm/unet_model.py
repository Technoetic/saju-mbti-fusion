"""ADR-217 - U-Net 아키텍처 (손금 선 semantic segmentation).

학술 근거:
  - Ronneberger et al. 2015 "U-Net: Convolutional Networks for Biomedical
    Image Segmentation" (원본 아키텍처)
  - milesial/Pytorch-UNet (GPL-3.0) — 표준 PyTorch 구현 참조
  - arXiv 2102.12127 "Efficient Palm-Line Segmentation with U-Net Context
    Fusion" F1 99.42% (Sun-Asterisk 사내 자료, 본 모듈은 표준 U-Net)

라이선스:
  ⚠ 본 아키텍처 구현은 milesial/Pytorch-UNet (GPL-3.0) 참조.
  운영 사용 시 GPL-3.0 라이선스 의무 (오픈소스화) 확인 필요.
  → ADR-216 사용자 결단 영역.

본 모듈은 PyTorch 가용 시만 import 가능 — unet_line_extractor.py 가 try/except로
로드 차단.

ADR 정합:
  - ADR-216 U-Net 인터페이스 (본 모듈 호출)
  - ADR-215 Gabor (PyTorch·가중치 부재 시 fallback)
  - ADR-006 자문 거절 (학파 명칭 X — 픽셀 마스크만)
"""

from __future__ import annotations

import torch
import torch.nn as nn
import torch.nn.functional as F


class _DoubleConv(nn.Module):
    """U-Net 표준 더블 컨볼루션 블록."""

    def __init__(self, in_channels: int, out_channels: int):
        super().__init__()
        self.double_conv = nn.Sequential(
            nn.Conv2d(in_channels, out_channels, kernel_size=3, padding=1, bias=False),
            nn.BatchNorm2d(out_channels),
            nn.ReLU(inplace=True),
            nn.Conv2d(out_channels, out_channels, kernel_size=3, padding=1, bias=False),
            nn.BatchNorm2d(out_channels),
            nn.ReLU(inplace=True),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.double_conv(x)


class _Down(nn.Module):
    """Max pool + double conv (encoder)."""

    def __init__(self, in_channels: int, out_channels: int):
        super().__init__()
        self.maxpool_conv = nn.Sequential(
            nn.MaxPool2d(2),
            _DoubleConv(in_channels, out_channels),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.maxpool_conv(x)


class _Up(nn.Module):
    """Upsample + double conv (decoder) + skip connection."""

    def __init__(self, in_channels: int, out_channels: int, bilinear: bool = True):
        super().__init__()
        if bilinear:
            self.up = nn.Upsample(scale_factor=2, mode="bilinear", align_corners=True)
            self.conv = _DoubleConv(in_channels, out_channels)
        else:
            self.up = nn.ConvTranspose2d(in_channels // 2, in_channels // 2,
                                         kernel_size=2, stride=2)
            self.conv = _DoubleConv(in_channels, out_channels)

    def forward(self, x1: torch.Tensor, x2: torch.Tensor) -> torch.Tensor:
        x1 = self.up(x1)
        # 크기 정합 (홀수 입력 대응)
        diff_y = x2.size(2) - x1.size(2)
        diff_x = x2.size(3) - x1.size(3)
        x1 = F.pad(x1, [diff_x // 2, diff_x - diff_x // 2,
                        diff_y // 2, diff_y - diff_y // 2])
        x = torch.cat([x2, x1], dim=1)
        return self.conv(x)


class _OutConv(nn.Module):
    def __init__(self, in_channels: int, out_channels: int):
        super().__init__()
        self.conv = nn.Conv2d(in_channels, out_channels, kernel_size=1)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.conv(x)


class UNet(nn.Module):
    """U-Net (Ronneberger et al. 2015) — 손금 선 semantic segmentation.

    Args:
        n_channels: 입력 채널 (RGB=3)
        n_classes: 출력 채널 (binary line mask=1)
        bilinear: bilinear upsample 사용 여부 (True 권장)

    Note:
        본 구현은 milesial/Pytorch-UNet (GPL-3.0) 참조.
        운영 사용 시 라이선스 의무 확인 필요 (ADR-216 사용자 결단).
    """

    def __init__(self, n_channels: int = 3, n_classes: int = 1, bilinear: bool = True):
        super().__init__()
        self.n_channels = n_channels
        self.n_classes = n_classes
        self.bilinear = bilinear

        self.inc = _DoubleConv(n_channels, 64)
        self.down1 = _Down(64, 128)
        self.down2 = _Down(128, 256)
        self.down3 = _Down(256, 512)
        factor = 2 if bilinear else 1
        self.down4 = _Down(512, 1024 // factor)
        self.up1 = _Up(1024, 512 // factor, bilinear)
        self.up2 = _Up(512, 256 // factor, bilinear)
        self.up3 = _Up(256, 128 // factor, bilinear)
        self.up4 = _Up(128, 64, bilinear)
        self.outc = _OutConv(64, n_classes)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        x1 = self.inc(x)
        x2 = self.down1(x1)
        x3 = self.down2(x2)
        x4 = self.down3(x3)
        x5 = self.down4(x4)
        x = self.up1(x5, x4)
        x = self.up2(x, x3)
        x = self.up3(x, x2)
        x = self.up4(x, x1)
        return self.outc(x)
