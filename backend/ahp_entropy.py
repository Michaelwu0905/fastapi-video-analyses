from __future__ import annotations

import math
from typing import Any

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

ALL_INDICATORS = [name for cfg in CRITERIA.values() for name in cfg["indicators"]]


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

    column_sums = normalized.sum(axis=0)
    proportion = np.zeros_like(normalized, dtype=float)
    for j in range(normalized.shape[1]):
        if math.isclose(column_sums[j], 0.0):
            proportion[:, j] = 0.0
        else:
            proportion[:, j] = normalized[:, j] / column_sums[j]

    m = data.shape[0]
    k = 1.0 / math.log(m) if m > 1 else 0.0
    entropy = np.zeros(normalized.shape[1], dtype=float)
    for j in range(normalized.shape[1]):
        col = proportion[:, j]
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


def build_ahp_weights() -> tuple[dict[str, float], dict[str, dict[str, float]], dict[str, dict[str, float]], dict[str, dict[str, float]]]:
    criteria_names = list(CRITERIA.keys())
    criteria_weight_values, lambda_max, ci, cr = ahp_weights(CRITERIA_MATRIX)
    criteria_weights = {
        name: float(criteria_weight_values[idx])
        for idx, name in enumerate(criteria_names)
    }
    criteria_meta = {
        "lambda_max": lambda_max,
        "ci": ci,
        "cr": cr,
    }

    local_weights: dict[str, dict[str, float]] = {}
    global_weights: dict[str, dict[str, float]] = {}
    consistency: dict[str, dict[str, float]] = {"criteria": criteria_meta}
    for criterion_name, cfg in CRITERIA.items():
        local_weight_values, lambda_max, ci, cr = ahp_weights(cfg["matrix"])
        local_weights[criterion_name] = {}
        global_weights[criterion_name] = {}
        consistency[criterion_name] = {
            "lambda_max": lambda_max,
            "ci": ci,
            "cr": cr,
        }
        for idx, indicator in enumerate(cfg["indicators"]):
            local_weight = float(local_weight_values[idx])
            local_weights[criterion_name][indicator] = local_weight
            global_weights[criterion_name][indicator] = local_weight * criteria_weights[criterion_name]
    return criteria_weights, local_weights, global_weights, consistency


def flatten_global_weights(global_weights: dict[str, dict[str, float]]) -> np.ndarray:
    values: list[float] = []
    for criterion_name in CRITERIA.keys():
        for indicator in CRITERIA[criterion_name]["indicators"]:
            values.append(global_weights[criterion_name][indicator])
    arr = np.array(values, dtype=float)
    return arr / arr.sum()


def build_metric_row(item: dict[str, Any]) -> list[float]:
    return [float(item.get(indicator, 0) or 0) for indicator in ALL_INDICATORS]


def score_to_level(score: float) -> str:
    if score >= 80:
        return "高传播力"
    if score >= 60:
        return "中传播力"
    return "低传播力"


def evaluate_video_with_samples(
    current_item: dict[str, Any],
    sample_items: list[dict[str, Any]],
    alpha: float = 0.5,
) -> dict[str, Any]:
    if not sample_items:
        raise ValueError("缺少样本数据，无法计算 AHP + 熵权法结果")

    sample_map = {item["bvid"]: item for item in sample_items if item.get("bvid")}
    sample_map[current_item["bvid"]] = current_item
    merged_items = list(sample_map.values())

    if len(merged_items) < 3:
        raise ValueError("样本数量不足，至少需要 3 条样本记录")

    data = np.array([build_metric_row(item) for item in merged_items], dtype=float)
    normalized, entropy, entropy_weight_vector = entropy_weights(data)

    criteria_weights, _, global_weights_nested, consistency = build_ahp_weights()
    ahp_weight_vector = flatten_global_weights(global_weights_nested)
    combined_weight_vector = alpha * ahp_weight_vector + (1 - alpha) * entropy_weight_vector
    combined_weight_vector = combined_weight_vector / combined_weight_vector.sum()

    total_scores = normalized @ combined_weight_vector * 100
    current_index = next(idx for idx, item in enumerate(merged_items) if item["bvid"] == current_item["bvid"])
    current_score = float(total_scores[current_index])

    criteria_scores: dict[str, float] = {}
    for criterion_name, cfg in CRITERIA.items():
        indices = [ALL_INDICATORS.index(ind) for ind in cfg["indicators"]]
        weights = np.array([combined_weight_vector[idx] for idx in indices], dtype=float)
        if not math.isclose(weights.sum(), 0.0):
            weights = weights / weights.sum()
        criteria_scores[criterion_name] = float((normalized[current_index, indices] @ weights) * 100)

    ranked_indices = np.argsort(-total_scores)
    rank = int(np.where(ranked_indices == current_index)[0][0]) + 1

    indicator_rows = []
    for idx, indicator in enumerate(ALL_INDICATORS):
        contribution = float(normalized[current_index, idx] * combined_weight_vector[idx] * 100)
        indicator_rows.append({
            "key": indicator,
            "name": INDICATOR_LABELS[indicator],
            "value": float(build_metric_row(current_item)[idx]),
            "ahp_weight": float(ahp_weight_vector[idx]),
            "entropy_weight": float(entropy_weight_vector[idx]),
            "combined_weight": float(combined_weight_vector[idx]),
            "contribution": contribution,
        })

    indicator_rows.sort(key=lambda item: item["contribution"], reverse=True)

    return {
        "status": "success",
        "total_score": round(current_score, 2),
        "level": score_to_level(current_score),
        "rank": rank,
        "sample_size": len(merged_items),
        "alpha": alpha,
        "dimension_scores": {
            "breadth": round(criteria_scores["breadth"], 2),
            "depth": round(criteria_scores["depth"], 2),
            "recognition": round(criteria_scores["recognition"], 2),
            "knowledge_effect": round(criteria_scores["knowledge_effect"], 2),
        },
        "criteria_weights": {
            key: round(value, 4) for key, value in criteria_weights.items()
        },
        "consistency": {
            key: {name: round(val, 4) for name, val in meta.items()}
            for key, meta in consistency.items()
        },
        "indicator_rows": [
            {
                **row,
                "ahp_weight": round(row["ahp_weight"], 4),
                "entropy_weight": round(row["entropy_weight"], 4),
                "combined_weight": round(row["combined_weight"], 4),
                "contribution": round(row["contribution"], 2),
            }
            for row in indicator_rows
        ],
    }
