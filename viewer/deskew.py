"""スキャン画像の傾き角推定（射影プロファイル法）。numpy + Pillow のみ使用。

文字行が水平に揃うと、水平方向の射影（行ごとの黒画素量）の分散が最大になる。
候補角でグレースケール画像を回転し、行和の分散が最大の角度を傾き角とする。
"""
from __future__ import annotations

import numpy as np
from PIL import Image


def estimate_skew(gray: Image.Image, limit: float = 8.0,
                  step: float = 0.5, max_dim: int = 900) -> float:
    """グレースケール画像の傾き角（度）を返す。この角度だけ回転すると水平になる。"""
    g = gray.convert("L")
    w, h = g.size
    scale = max_dim / max(w, h)
    if scale < 1.0:
        g = g.resize((max(1, int(w * scale)), max(1, int(h * scale))))

    best_angle, best_score = 0.0, -1.0
    angle = -limit
    while angle <= limit + 1e-9:
        rot = g.rotate(angle, resample=Image.Resampling.BILINEAR, fillcolor=255)
        ink = 255.0 - np.asarray(rot, dtype=np.float32)  # 黒いほど大
        rowsum = ink.sum(axis=1)
        score = float(np.var(rowsum))
        if score > best_score:
            best_score, best_angle = score, angle
        angle += step
    return best_angle
