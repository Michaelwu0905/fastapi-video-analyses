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
CRITERIA_SYMBOLS = {
    "breadth": "B",
    "depth": "D",
    "recognition": "R",
    "knowledge_effect": "K",
}

METRIC_DEFINITIONS = {
    "daily_views": r"X_{1} = \frac{V}{A}",
    "share_rate": r"X_{2} = \frac{S}{V}",
    "reply_rate": r"X_{3} = \frac{R}{V}",
    "danmaku_density": r"X_{4} = \frac{D}{T}",
    "composite_interaction_rate": r"X_{5} = \frac{L + C + F + S + R}{V}",
    "like_rate": r"X_{6} = \frac{L}{V}",
    "coin_rate": r"X_{7} = \frac{C}{V}",
    "favorite_rate": r"X_{8} = \frac{F}{V}",
    "recognition_rate": r"X_{9} = \frac{L + C + F}{V}",
    "cognitive_feedback_ratio": r"X_{10} = \frac{N_{cf}}{N_{all}}",
    "question_comment_ratio": r"X_{11} = \frac{N_q}{N_{all}}",
    "sentiment_polarization": r"X_{12} = \frac{N_{pos} + N_{neg}}{N_{all}}",
}

SYMBOL_NOTES = [
    {"symbol": "V", "label": "播放量", "description": "视频累计播放次数", "field": "view_count"},
    {"symbol": "L", "label": "点赞量", "description": "视频累计点赞次数", "field": "like_count"},
    {"symbol": "C", "label": "投币量", "description": "B站用户对视频的累计投币次数", "field": "coin_count"},
    {"symbol": "F", "label": "收藏量", "description": "视频被用户收藏的次数", "field": "favorite_count"},
    {"symbol": "S", "label": "分享量", "description": "视频被用户分享的次数", "field": "share_count"},
    {"symbol": "R", "label": "评论量", "description": "视频评论区的评论数量", "field": "reply_count"},
    {"symbol": "D", "label": "弹幕量", "description": "视频累计弹幕数量", "field": "danmaku_count"},
    {"symbol": "T", "label": "视频时长", "description": "视频总时长，单位为秒", "field": "duration_seconds", "unit": "秒"},
    {"symbol": "A", "label": "存续天数", "description": "视频发布至分析时刻的天数", "field": "age_days", "unit": "天"},
    {"symbol": "N_cf", "label": "认知反馈评论数", "description": "表达学到了、看懂了等知识获得感的评论数量", "field": "cognitive_feedback_count"},
    {"symbol": "N_q", "label": "问题型评论数", "description": "包含提问、追问、求解释等表达的评论数量", "field": "question_comment_count"},
    {"symbol": "N_pos", "label": "正向评论数", "description": "情感分析结果为正向的评论数量", "field": "positive_comment_count"},
    {"symbol": "N_neg", "label": "负向评论数", "description": "情感分析结果为负向的评论数量", "field": "negative_comment_count"},
    {"symbol": "N_all", "label": "评论总数", "description": "参与知识传播效果统计的评论总数量", "field": "analyzed_comment_count", "fallback_field": "saved_comments_count"},
]


def round4(value: float) -> float:
    return round(float(value), 4)


def round2(value: float) -> float:
    return round(float(value), 2)


def latex_num(value: float, digits: int = 4) -> str:
    rounded = round(float(value), digits)
    if math.isclose(rounded, 0.0, abs_tol=10 ** (-(digits + 1))):
        rounded = 0.0
    return f"{rounded:g}"


def latex_matrix(matrix: np.ndarray) -> str:
    rows = [
        " & ".join(latex_num(value) for value in row)
        for row in matrix
    ]
    return r"\begin{bmatrix}" + r" \\ ".join(rows) + r"\end{bmatrix}"


def latex_vector(values: list[float] | np.ndarray, digits: int = 4) -> str:
    return r"\begin{bmatrix}" + r" \\ ".join(latex_num(value, digits) for value in values) + r"\end{bmatrix}"


def build_symbol_notes(current_item: dict[str, Any]) -> list[dict[str, Any]]:
    notes: list[dict[str, Any]] = []
    for note in SYMBOL_NOTES:
        item = {
            "symbol": note["symbol"],
            "label": note["label"],
            "description": note["description"],
        }
        field = note.get("field")
        if field:
            value = current_item.get(field, 0) or 0
            if not value and note.get("fallback_field"):
                value = current_item.get(note["fallback_field"], 0) or 0
            unit = note.get("unit", "")
            item["value"] = value
            item["value_label"] = f"{value}{unit}" if unit else str(value)
        else:
            item["value_note"] = note.get("note", "当前没有可展示的原始值")
        notes.append(item)
    return notes


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
    min_vals = data.min(axis=0)
    max_vals = data.max(axis=0)
    ranges = max_vals - min_vals

    criteria_weights, local_weights_nested, global_weights_nested, consistency = build_ahp_weights()
    ahp_weight_vector = flatten_global_weights(global_weights_nested)
    combined_weight_vector = alpha * ahp_weight_vector + (1 - alpha) * entropy_weight_vector
    combined_weight_vector = combined_weight_vector / combined_weight_vector.sum()

    total_scores = normalized @ combined_weight_vector * 100
    current_index = next(idx for idx, item in enumerate(merged_items) if item["bvid"] == current_item["bvid"])
    current_score = float(total_scores[current_index])
    current_metric_row = build_metric_row(current_item)

    criteria_scores: dict[str, float] = {}
    dimension_formulas: list[dict[str, Any]] = []
    for criterion_name, cfg in CRITERIA.items():
        indices = [ALL_INDICATORS.index(ind) for ind in cfg["indicators"]]
        dimension_weights = np.array([combined_weight_vector[idx] for idx in indices], dtype=float)
        if not math.isclose(dimension_weights.sum(), 0.0):
            dimension_weights = dimension_weights / dimension_weights.sum()
        dimension_score = float((normalized[current_index, indices] @ dimension_weights) * 100)
        criteria_scores[criterion_name] = dimension_score

        items: list[dict[str, Any]] = []
        term_fragments: list[str] = []
        for local_idx, global_idx in enumerate(indices):
            indicator = ALL_INDICATORS[global_idx]
            normalized_value = float(normalized[current_index, global_idx])
            dimension_weight = float(dimension_weights[local_idx])
            items.append({
                "key": indicator,
                "name": INDICATOR_LABELS[indicator],
                "normalized_value": round4(normalized_value),
                "combined_weight": round4(float(combined_weight_vector[global_idx])),
                "dimension_weight": round4(dimension_weight),
                "local_ahp_weight": round4(local_weights_nested[criterion_name][indicator]),
            })
            term_fragments.append(f"{round4(normalized_value)} × {round4(dimension_weight)}")

        dimension_formulas.append({
            "key": criterion_name,
            "name": cfg["label"],
            "criteria_weight": round4(criteria_weights[criterion_name]),
            "score": round2(dimension_score),
            "formula_text": f"{cfg['label']} = ({' + '.join(term_fragments)}) × 100 = {round2(dimension_score)}",
            "items": items,
        })

    ranked_indices = np.argsort(-total_scores)
    rank = int(np.where(ranked_indices == current_index)[0][0]) + 1

    indicator_rows = []
    raw_metrics = []
    normalized_metrics = []
    weight_metrics = []
    total_terms: list[dict[str, Any]] = []
    total_formula_fragments: list[str] = []
    for idx, indicator in enumerate(ALL_INDICATORS):
        contribution = float(normalized[current_index, idx] * combined_weight_vector[idx] * 100)
        criterion_name = next(
            name for name, cfg in CRITERIA.items()
            if indicator in cfg["indicators"]
        )
        raw_value = float(current_metric_row[idx])
        min_value = float(min_vals[idx])
        max_value = float(max_vals[idx])
        range_value = float(ranges[idx])
        normalized_value = float(normalized[current_index, idx])
        ahp_weight = float(ahp_weight_vector[idx])
        entropy_weight = float(entropy_weight_vector[idx])
        combined_weight = float(combined_weight_vector[idx])

        row = {
            "key": indicator,
            "name": INDICATOR_LABELS[indicator],
            "value": raw_value,
            "criterion": criterion_name,
            "criterion_label": CRITERIA[criterion_name]["label"],
            "ahp_weight": ahp_weight,
            "entropy_weight": entropy_weight,
            "combined_weight": combined_weight,
            "contribution": contribution,
        }
        indicator_rows.append(row)

        raw_metrics.append({
            "key": indicator,
            "name": INDICATOR_LABELS[indicator],
            "criterion": criterion_name,
            "criterion_label": CRITERIA[criterion_name]["label"],
            "value": round4(raw_value),
        })

        if math.isclose(range_value, 0.0):
            normalized_formula_text = f"{INDICATOR_LABELS[indicator]}: 样本极差为 0，标准化结果记为 0"
        else:
            normalized_formula_text = (
                f"{INDICATOR_LABELS[indicator]}: ({round4(raw_value)} - {round4(min_value)}) / "
                f"({round4(max_value)} - {round4(min_value)}) = {round4(normalized_value)}"
            )
        normalized_metrics.append({
            "key": indicator,
            "name": INDICATOR_LABELS[indicator],
            "criterion": criterion_name,
            "criterion_label": CRITERIA[criterion_name]["label"],
            "raw_value": round4(raw_value),
            "min_value": round4(min_value),
            "max_value": round4(max_value),
            "range_value": round4(range_value),
            "normalized_value": round4(normalized_value),
            "formula_text": normalized_formula_text,
            "is_constant": math.isclose(range_value, 0.0),
        })

        weight_metrics.append({
            "key": indicator,
            "name": INDICATOR_LABELS[indicator],
            "criterion": criterion_name,
            "criterion_label": CRITERIA[criterion_name]["label"],
            "alpha": round4(alpha),
            "ahp_weight": round4(ahp_weight),
            "entropy_weight": round4(entropy_weight),
            "combined_weight": round4(combined_weight),
            "formula_text": (
                f"{INDICATOR_LABELS[indicator]}: {round4(alpha)} × {round4(ahp_weight)} + "
                f"{round4(1 - alpha)} × {round4(entropy_weight)} = {round4(combined_weight)}"
            ),
        })

        total_terms.append({
            "key": indicator,
            "name": INDICATOR_LABELS[indicator],
            "criterion": criterion_name,
            "criterion_label": CRITERIA[criterion_name]["label"],
            "normalized_value": round4(normalized_value),
            "combined_weight": round4(combined_weight),
            "contribution": round2(contribution),
        })
        total_formula_fragments.append(
            f"{round4(normalized_value)} × {round4(combined_weight)} × 100"
        )

    indicator_rows.sort(key=lambda item: item["contribution"], reverse=True)
    total_terms.sort(key=lambda item: item["contribution"], reverse=True)

    grouped_raw_metrics = {
        criterion_name: [item for item in raw_metrics if item["criterion"] == criterion_name]
        for criterion_name in CRITERIA.keys()
    }
    grouped_normalized_metrics = {
        criterion_name: [item for item in normalized_metrics if item["criterion"] == criterion_name]
        for criterion_name in CRITERIA.keys()
    }
    grouped_weight_metrics = {
        criterion_name: [item for item in weight_metrics if item["criterion"] == criterion_name]
        for criterion_name in CRITERIA.keys()
    }
    criteria_names = list(CRITERIA.keys())
    criteria_weight_vector = [criteria_weights[name] for name in criteria_names]
    criteria_consistency = consistency["criteria"]
    latex_indicator_matrices = []
    for criterion_name, cfg in CRITERIA.items():
        criterion_symbol = CRITERIA_SYMBOLS[criterion_name]
        indicators = cfg["indicators"]
        local_weights = [local_weights_nested[criterion_name][indicator] for indicator in indicators]
        latex_indicator_matrices.append({
            "key": criterion_name,
            "name": cfg["label"],
            "indicator_names": [INDICATOR_LABELS[indicator] for indicator in indicators],
            "matrix": rf"A_{{{criterion_symbol}}} = {latex_matrix(cfg['matrix'])}",
            "local_weight_vector": rf"w_{{{criterion_symbol}}} = {latex_vector(local_weights)}",
            "consistency": (
                rf"CI=\frac{{\lambda_{{max}}-n}}{{n-1}}"
                rf"=\frac{{{latex_num(consistency[criterion_name]['lambda_max'])}-{len(indicators)}}}{{{max(len(indicators) - 1, 1)}}}"
                rf"={latex_num(consistency[criterion_name]['ci'])},\quad "
                rf"CR={latex_num(consistency[criterion_name]['cr'])}"
            ),
        })

    latex_metric_definitions = [
        {
            "key": indicator,
            "name": INDICATOR_LABELS[indicator],
            "formula": METRIC_DEFINITIONS[indicator],
        }
        for indicator in ALL_INDICATORS
    ]

    latex_normalization = []
    latex_entropy_weights = []
    latex_combined_weights = []
    for idx, indicator in enumerate(ALL_INDICATORS):
        raw_value = current_metric_row[idx]
        min_value = float(min_vals[idx])
        max_value = float(max_vals[idx])
        normalized_value = float(normalized[current_index, idx])
        if math.isclose(float(ranges[idx]), 0.0):
            normalization_formula = (
                rf"z_{{{idx + 1}}}=0,\quad "
                rf"\max(X_{{{idx + 1}}})-\min(X_{{{idx + 1}}})=0"
            )
        else:
            normalization_formula = (
                rf"z_{{{idx + 1}}}=\frac{{{latex_num(raw_value)}-{latex_num(min_value)}}}"
                rf"{{{latex_num(max_value)}-{latex_num(min_value)}}}"
                rf"={latex_num(normalized_value)}"
            )
        latex_normalization.append({
            "key": indicator,
            "name": INDICATOR_LABELS[indicator],
            "formula": normalization_formula,
        })

        divergence_value = float(1 - entropy[idx])
        latex_entropy_weights.append({
            "key": indicator,
            "name": INDICATOR_LABELS[indicator],
            "formula": (
                rf"e_{{{idx + 1}}}={latex_num(float(entropy[idx]))},\quad "
                rf"d_{{{idx + 1}}}=1-e_{{{idx + 1}}}={latex_num(divergence_value)},\quad "
                rf"w^E_{{{idx + 1}}}={latex_num(float(entropy_weight_vector[idx]))}"
            ),
        })

        latex_combined_weights.append({
            "key": indicator,
            "name": INDICATOR_LABELS[indicator],
            "formula": (
                rf"w_{{{idx + 1}}}={latex_num(alpha)}\times {latex_num(float(ahp_weight_vector[idx]))}"
                rf"+{latex_num(1 - alpha)}\times {latex_num(float(entropy_weight_vector[idx]))}"
                rf"={latex_num(float(combined_weight_vector[idx]))}"
            ),
        })

    latex_dimension_scores = []
    for dimension in dimension_formulas:
        criterion_symbol = CRITERIA_SYMBOLS[dimension["key"]]
        terms = []
        for item in dimension["items"]:
            terms.append(
                rf"{latex_num(item['normalized_value'])}\times {latex_num(item['dimension_weight'])}"
            )
        latex_dimension_scores.append({
            "key": dimension["key"],
            "name": dimension["name"],
            "formula": rf"S_{{{criterion_symbol}}}=\left({' + '.join(terms)}\right)\times 100={latex_num(dimension['score'], 2)}",
        })

    total_latex_terms = []
    contribution_latex_rows = []
    for idx, indicator in enumerate(ALL_INDICATORS):
        contribution = float(normalized[current_index, idx] * combined_weight_vector[idx] * 100)
        total_latex_terms.append(
            rf"{latex_num(float(normalized[current_index, idx]))}\times {latex_num(float(combined_weight_vector[idx]))}"
        )
        contribution_latex_rows.append({
            "key": indicator,
            "name": INDICATOR_LABELS[indicator],
            "formula": (
                rf"C_{{{idx + 1}}}={latex_num(float(normalized[current_index, idx]))}"
                rf"\times {latex_num(float(combined_weight_vector[idx]))}\times 100"
                rf"={latex_num(contribution, 2)}"
            ),
        })

    latex_view = {
        "symbol_notes": build_symbol_notes(current_item),
        "metric_definitions": latex_metric_definitions,
        "ahp": {
            "criteria_matrix": rf"A={latex_matrix(CRITERIA_MATRIX)}",
            "criteria_weight_vector": rf"w^A_c={latex_vector(criteria_weight_vector)}",
            "criteria_consistency": (
                rf"CI=\frac{{\lambda_{{max}}-n}}{{n-1}}"
                rf"=\frac{{{latex_num(criteria_consistency['lambda_max'])}-4}}{{3}}"
                rf"={latex_num(criteria_consistency['ci'])},\quad "
                rf"CR=\frac{{CI}}{{RI}}={latex_num(criteria_consistency['cr'])}"
            ),
            "indicator_matrices": latex_indicator_matrices,
        },
        "entropy": {
            "standardization_formula": r"z_{ij}=\frac{x_{ij}-\min(x_j)}{\max(x_j)-\min(x_j)}",
            "proportion_formula": r"p_{ij}=\frac{z_{ij}}{\sum_{i=1}^{m}z_{ij}}",
            "entropy_formula": r"e_j=-\frac{1}{\ln m}\sum_{i=1}^{m}p_{ij}\ln p_{ij}",
            "divergence_formula": r"d_j=1-e_j",
            "weight_formula": r"w_j^E=\frac{d_j}{\sum_{j=1}^{n}d_j}",
            "normalization_rows": latex_normalization,
            "weight_rows": latex_entropy_weights,
        },
        "combined_weights": {
            "formula": r"w_j=\alpha w_j^A+(1-\alpha)w_j^E",
            "rows": latex_combined_weights,
        },
        "dimension_scores": latex_dimension_scores,
        "total_score": {
            "formula": rf"S=\left({' + '.join(total_latex_terms)}\right)\times 100={latex_num(current_score, 2)}",
            "contribution_rows": contribution_latex_rows,
        },
    }

    return {
        "status": "success",
        "total_score": round2(current_score),
        "level": score_to_level(current_score),
        "rank": rank,
        "sample_size": len(merged_items),
        "alpha": alpha,
        "dimension_scores": {
            "breadth": round2(criteria_scores["breadth"]),
            "depth": round2(criteria_scores["depth"]),
            "recognition": round2(criteria_scores["recognition"]),
            "knowledge_effect": round2(criteria_scores["knowledge_effect"]),
        },
        "criteria_weights": {
            key: round4(value) for key, value in criteria_weights.items()
        },
        "consistency": {
            key: {name: round4(val) for name, val in meta.items()}
            for key, meta in consistency.items()
        },
        "indicator_rows": [
            {
                **row,
                "ahp_weight": round4(row["ahp_weight"]),
                "entropy_weight": round4(row["entropy_weight"]),
                "combined_weight": round4(row["combined_weight"]),
                "contribution": round2(row["contribution"]),
            }
            for row in indicator_rows
        ],
        "formula_view": {
            "raw_metrics": grouped_raw_metrics,
            "normalized_metrics": grouped_normalized_metrics,
            "weight_metrics": grouped_weight_metrics,
            "dimension_formulas": dimension_formulas,
            "total_formula": {
                "terms": total_terms,
                "formula_text": (
                    f"综合传播力得分 = {' + '.join(total_formula_fragments)} = {round2(current_score)}"
                ),
                "score": round2(current_score),
            },
            "latex_view": latex_view,
        },
    }
