#!/usr/bin/env python3
"""
对 B 站科普视频样本运行一版 AHP + 熵权法。

用法示例：
    python backend/scripts/ahp_entropy_analysis.py \
        --input sample_metrics.csv \
        --output scores.csv

也可以先导出模板：
    python backend/scripts/ahp_entropy_analysis.py --export-template sample_metrics.csv
"""

from __future__ import annotations

import argparse
import csv
import math
from pathlib import Path
from typing import Iterable

import numpy as np


RI_TABLE = {
    1: 0.0,
    2: 0.0,
    3: 0.58,
    4: 0.90,
    5: 1.12,
    6: 1.24,
    7: 1.32,
    8: 1.41,
    9: 1.45,
    10: 1.49,
}


CRITERIA = {
    "breadth": {
        "label": "传播广度",
        "indicators": ["daily_views", "share_rate"],
        "matrix": np.array([
            [1, 2],
            [1 / 2, 1],
        ], dtype=float),
    },
    "depth": {
        "label": "互动深度",
        "indicators": ["reply_rate", "danmaku_density", "composite_interaction_rate"],
        "matrix": np.array([
            [1, 1 / 2, 1 / 3],
            [2, 1, 1 / 2],
            [3, 2, 1],
        ], dtype=float),
    },
    "recognition": {
        "label": "传播认同",
        "indicators": ["like_rate", "coin_rate", "favorite_rate", "recognition_rate"],
        "matrix": np.array([
            [1, 1 / 3, 1 / 3, 1 / 4],
            [3, 1, 1, 1 / 2],
            [3, 1, 1, 1 / 2],
            [4, 2, 2, 1],
        ], dtype=float),
    },
    "knowledge_effect": {
        "label": "知识传播效果",
        "indicators": ["cognitive_feedback_ratio", "question_comment_ratio", "sentiment_polarization"],
        "matrix": np.array([
            [1, 2, 4],
            [1 / 2, 1, 3],
            [1 / 4, 1 / 3, 1],
        ], dtype=float),
    },
}

CRITERIA_MATRIX = np.array([
    [1, 1 / 2, 1 / 3, 1 / 4],
    [2, 1, 1 / 2, 1 / 3],
    [3, 2, 1, 1 / 2],
    [4, 3, 2, 1],
], dtype=float)

INDICATOR_LABELS = {
    "daily_views": "单位天播放量",
    "share_rate": "分享率",
    "reply_rate": "评论率",
    "danmaku_density": "弹幕密度",
    "composite_interaction_rate": "复合互动率",
    "like_rate": "点赞率",
    "coin_rate": "投币率",
    "favorite_rate": "收藏率",
    "recognition_rate": "认同效率",
    "cognitive_feedback_ratio": "认知反馈占比",
    "question_comment_ratio": "问题型评论占比",
    "sentiment_polarization": "情感极化度",
}

ID_COLUMNS = ["bvid", "title"]
ALL_INDICATORS = [name for cfg in CRITERIA.values() for name in cfg["indicators"]]
TEMPLATE_HEADERS = ID_COLUMNS + ALL_INDICATORS
BACKEND_DIR = Path(__file__).resolve().parent.parent
DEFAULT_TEMPLATE_PATH = BACKEND_DIR / "ahp_metrics_template.csv"
DEFAULT_OUTPUT_PATH = BACKEND_DIR / "ahp_entropy_scores.csv"


def export_template(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.writer(fh)
        writer.writerow(TEMPLATE_HEADERS)
        writer.writerow([
            "BV示例",
            "示例视频",
            12000,
            0.012,
            0.008,
            24.5,
            0.026,
            0.041,
            0.006,
            0.009,
            0.027,
            0.180,
            0.220,
            0.640,
        ])


def load_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", newline="", encoding="utf-8-sig") as fh:
        rows = list(csv.DictReader(fh))
    if not rows:
        raise ValueError("输入 CSV 为空")
    missing = [col for col in TEMPLATE_HEADERS if col not in rows[0]]
    if missing:
        raise ValueError(f"输入 CSV 缺少字段：{', '.join(missing)}")
    return rows


def build_data_matrix(rows: list[dict[str, str]]) -> np.ndarray:
    data: list[list[float]] = []
    for row in rows:
        values = []
        for col in ALL_INDICATORS:
            raw = row.get(col, "").strip()
            if raw == "":
                raise ValueError(f"样本 {row.get('bvid') or row.get('title') or '<unknown>'} 缺少指标 {col}")
            values.append(float(raw))
        data.append(values)
    return np.array(data, dtype=float)


def ahp_weights(matrix: np.ndarray) -> tuple[np.ndarray, float, float, float]:
    eigvals, eigvecs = np.linalg.eig(matrix)
    max_idx = int(np.argmax(eigvals.real))
    max_eigval = float(eigvals[max_idx].real)
    weights = np.abs(eigvecs[:, max_idx].real)
    weights = weights / weights.sum()

    n = matrix.shape[0]
    if n <= 2:
        return weights, max_eigval, 0.0, 0.0

    ci = (max_eigval - n) / (n - 1)
    ri = RI_TABLE[n]
    cr = ci / ri if ri else 0.0
    return weights, max_eigval, ci, cr


def entropy_weights(data: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    min_vals = data.min(axis=0)
    max_vals = data.max(axis=0)
    ranges = max_vals - min_vals

    normalized = np.zeros_like(data, dtype=float)
    for j in range(data.shape[1]):
        if math.isclose(ranges[j], 0.0):
            normalized[:, j] = 0.0
        else:
            normalized[:, j] = (data[:, j] - min_vals[j]) / ranges[j]

    # 避免全零列导致后续除零；常数列最终应当得到 0 权重
    column_sums = normalized.sum(axis=0)
    p = np.zeros_like(normalized, dtype=float)
    for j in range(normalized.shape[1]):
        if math.isclose(column_sums[j], 0.0):
            p[:, j] = 0.0
        else:
            p[:, j] = normalized[:, j] / column_sums[j]

    m = data.shape[0]
    k = 1.0 / math.log(m) if m > 1 else 0.0

    entropy = np.zeros(normalized.shape[1], dtype=float)
    for j in range(normalized.shape[1]):
        col = p[:, j]
        valid = col > 0
        if not np.any(valid):
            entropy[j] = 1.0
        else:
            entropy[j] = -k * np.sum(col[valid] * np.log(col[valid]))

    divergence = 1.0 - entropy
    if math.isclose(divergence.sum(), 0.0):
        weights = np.full_like(divergence, 1.0 / len(divergence))
    else:
        weights = divergence / divergence.sum()
    return normalized, entropy, weights


def build_ahp_global_weights() -> tuple[dict[str, float], dict[str, dict[str, float]], dict[str, dict[str, float]]]:
    criteria_names = list(CRITERIA.keys())
    criteria_weight_values, _, _, _ = ahp_weights(CRITERIA_MATRIX)
    criteria_weights = {
        name: float(criteria_weight_values[idx])
        for idx, name in enumerate(criteria_names)
    }

    local_weights: dict[str, dict[str, float]] = {}
    global_weights: dict[str, dict[str, float]] = {}
    for criterion_name, cfg in CRITERIA.items():
        local_weight_values, _, _, _ = ahp_weights(cfg["matrix"])
        local_weights[criterion_name] = {}
        global_weights[criterion_name] = {}
        for idx, indicator in enumerate(cfg["indicators"]):
            local_weight = float(local_weight_values[idx])
            local_weights[criterion_name][indicator] = local_weight
            global_weights[criterion_name][indicator] = local_weight * criteria_weights[criterion_name]

    return criteria_weights, local_weights, global_weights


def flatten_global_weights(global_weights: dict[str, dict[str, float]]) -> np.ndarray:
    values: list[float] = []
    for criterion_name in CRITERIA.keys():
        for indicator in CRITERIA[criterion_name]["indicators"]:
            values.append(global_weights[criterion_name][indicator])
    arr = np.array(values, dtype=float)
    return arr / arr.sum()


def write_scores(
    path: Path,
    rows: list[dict[str, str]],
    criteria_scores: dict[str, np.ndarray],
    total_scores: np.ndarray,
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    headers = [
        "rank",
        "bvid",
        "title",
        "total_score",
        "breadth_score",
        "depth_score",
        "recognition_score",
        "knowledge_effect_score",
    ]
    enriched = []
    for idx, row in enumerate(rows):
        enriched.append({
            "bvid": row["bvid"],
            "title": row["title"],
            "total_score": total_scores[idx],
            "breadth_score": criteria_scores["breadth"][idx],
            "depth_score": criteria_scores["depth"][idx],
            "recognition_score": criteria_scores["recognition"][idx],
            "knowledge_effect_score": criteria_scores["knowledge_effect"][idx],
        })
    enriched.sort(key=lambda item: item["total_score"], reverse=True)

    with path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=headers)
        writer.writeheader()
        for rank, item in enumerate(enriched, start=1):
            writer.writerow({
                "rank": rank,
                "bvid": item["bvid"],
                "title": item["title"],
                "total_score": f"{item['total_score']:.4f}",
                "breadth_score": f"{item['breadth_score']:.4f}",
                "depth_score": f"{item['depth_score']:.4f}",
                "recognition_score": f"{item['recognition_score']:.4f}",
                "knowledge_effect_score": f"{item['knowledge_effect_score']:.4f}",
            })


def print_ahp_report() -> None:
    criteria_names = list(CRITERIA.keys())
    criteria_weights, local_weights, global_weights = build_ahp_global_weights()
    criteria_weight_values, lambda_max, ci, cr = ahp_weights(CRITERIA_MATRIX)

    print("=== AHP 一级维度权重 ===")
    print(f"lambda_max={lambda_max:.4f}, CI={ci:.4f}, CR={cr:.4f}")
    for idx, name in enumerate(criteria_names):
        print(f"- {CRITERIA[name]['label']}: {criteria_weight_values[idx]:.4f}")
    print()

    for criterion_name, cfg in CRITERIA.items():
        local_weight_values, lambda_max, ci, cr = ahp_weights(cfg["matrix"])
        print(f"=== {cfg['label']} 二级指标权重 ===")
        print(f"lambda_max={lambda_max:.4f}, CI={ci:.4f}, CR={cr:.4f}")
        for idx, indicator in enumerate(cfg["indicators"]):
            print(
                f"- {INDICATOR_LABELS[indicator]}: "
                f"局部权重={local_weight_values[idx]:.4f}, "
                f"全局AHP权重={global_weights[criterion_name][indicator]:.4f}"
            )
        print()


def criterion_score(
    normalized: np.ndarray,
    criterion_name: str,
    combined_indicator_weights: dict[str, float],
) -> np.ndarray:
    indices = [ALL_INDICATORS.index(ind) for ind in CRITERIA[criterion_name]["indicators"]]
    weights = np.array([combined_indicator_weights[ind] for ind in CRITERIA[criterion_name]["indicators"]], dtype=float)
    local_sum = weights.sum()
    if not math.isclose(local_sum, 0.0):
        weights = weights / local_sum
    return normalized[:, indices] @ weights * 100


def run_analysis(input_path: Path, output_path: Path, alpha: float) -> None:
    rows = load_csv(input_path)
    data = build_data_matrix(rows)

    criteria_weights, _, global_weights_nested = build_ahp_global_weights()
    ahp_weight_vector = flatten_global_weights(global_weights_nested)
    ahp_indicator_weights = {
        indicator: ahp_weight_vector[idx]
        for idx, indicator in enumerate(ALL_INDICATORS)
    }

    normalized, entropy, entropy_weight_vector = entropy_weights(data)
    combined_weight_vector = alpha * ahp_weight_vector + (1 - alpha) * entropy_weight_vector
    combined_weight_vector = combined_weight_vector / combined_weight_vector.sum()
    combined_indicator_weights = {
        indicator: combined_weight_vector[idx]
        for idx, indicator in enumerate(ALL_INDICATORS)
    }

    total_scores = normalized @ combined_weight_vector * 100
    criteria_scores = {
        criterion_name: criterion_score(normalized, criterion_name, combined_indicator_weights)
        for criterion_name in CRITERIA.keys()
    }
    write_scores(output_path, rows, criteria_scores, total_scores)

    print_ahp_report()
    print("=== 熵权法结果 ===")
    for idx, indicator in enumerate(ALL_INDICATORS):
        print(
            f"- {INDICATOR_LABELS[indicator]}: 熵值={entropy[idx]:.4f}, "
            f"熵权={entropy_weight_vector[idx]:.4f}"
        )
    print()

    print(f"=== 组合权重结果 (alpha={alpha:.2f}) ===")
    for indicator in ALL_INDICATORS:
        print(
            f"- {INDICATOR_LABELS[indicator]}: "
            f"AHP={ahp_indicator_weights[indicator]:.4f}, "
            f"Entropy={entropy_weight_vector[ALL_INDICATORS.index(indicator)]:.4f}, "
            f"Combined={combined_indicator_weights[indicator]:.4f}"
        )
    print()

    ranked = sorted(
        zip(rows, total_scores),
        key=lambda item: item[1],
        reverse=True,
    )
    print("=== 综合传播力排序 Top 10 ===")
    for rank, (row, score) in enumerate(ranked[:10], start=1):
        print(f"{rank:02d}. {row['bvid']} | {row['title']} | score={score:.4f}")

    print()
    print(f"评分结果已写入: {output_path}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="运行一版 AHP + 熵权法传播力评价")
    parser.add_argument("--input", type=Path, help=f"输入 CSV 文件路径，建议放在 backend 目录下，例如 {DEFAULT_TEMPLATE_PATH}")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT_PATH, help=f"输出评分 CSV 文件路径，默认 {DEFAULT_OUTPUT_PATH}")
    parser.add_argument("--alpha", type=float, default=0.5, help="AHP 权重占比，默认 0.5")
    parser.add_argument("--export-template", type=Path, nargs="?", const=DEFAULT_TEMPLATE_PATH, help=f"导出一个样本 CSV 模板后退出，默认导出到 {DEFAULT_TEMPLATE_PATH}")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.export_template:
        export_template(args.export_template)
        print(f"已导出模板: {args.export_template}")
        return

    if not args.input:
        raise SystemExit("请提供 --input，或使用 --export-template 先导出模板")

    if not (0 <= args.alpha <= 1):
        raise SystemExit("--alpha 必须在 0 到 1 之间")

    run_analysis(args.input, args.output, args.alpha)


if __name__ == "__main__":
    main()
