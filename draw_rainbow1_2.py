import matplotlib.patches
from matplotlib.colors import to_rgb
import numpy as np
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use("Agg")     # Cloud Run用（画面表示しない）


# Cloud Run用日本語フォント
matplotlib.rcParams['font.family'] = 'Noto Sans CJK JP'


base_colors = [
    "#AB47BC",
    "#29B6F6",
    "#7CB342",
    "#FDD835",
    "#F9A825",
    "#E53935"
]


# ===== 表示用ラベル変換 =====

label_map = {

    "家庭人": "家庭人\n(配偶者、親)"

}


def darker(color, factor=0.7):

    r, g, b = to_rgb(color)

    return (

        r * factor,

        g * factor,

        b * factor

    )


# ============================================
# FastAPIから呼ばれる関数
# ============================================

def draw_rainbow(

        obj,

        output_path

):

    all_ages = np.array(

        obj["all_ages"]

    )

    categories = obj["categories"]

    data = obj["data_ratio"]

    # ===== 描画 =====
    fig = plt.figure(figsize=(9, 9))
    ax = plt.subplot(111, polar=True)

    ax.set_theta_direction(-1)
    ax.set_theta_offset(np.pi)
    ax.set_thetamin(0)
    ax.set_thetamax(180)

    # =========================================================
    # ★ 修正：10歳と80歳の幅も他と同じにする
    # =========================================================
    edges = np.linspace(0, np.pi, len(all_ages) + 1)   # 境界（+1個）
    angles = (edges[:-1] + edges[1:]) / 2              # 各区画の中心
    width = edges[1] - edges[0]                        # 全区画同じ幅
    # =========================================================

    inner_blank = 2.0
    layer_height = 1.0

    for layer_idx, c in enumerate(categories):

        scores = np.array(data[c])  # scores は 0～1 の割合
        base = inner_blank + layer_idx * layer_height
        color = base_colors[layer_idx]
        line_color = darker(color)

        arc_linewidth = 1.5
        vertical_linewidth = 0.7

        # 0の時の薄い輪郭線
        zero_linewidth = 0.5
        zero_alpha = 0.25

        for i in range(len(scores)):

            height = scores[i] * layer_height

            # ===== 0のときは薄い円弧だけ描画 =====
            if np.isclose(scores[i], 0.0):
                theta_left = edges[i]
                theta_right = edges[i + 1]
                theta_arc = np.linspace(theta_left, theta_right, 60)
                r_arc = np.full_like(theta_arc, base)

                ax.plot(theta_arc, r_arc,
                        color=line_color,
                        linewidth=zero_linewidth,
                        alpha=zero_alpha)
                continue

            bars = ax.bar(angles[i],
                          height,
                          width=width,
                          bottom=base,
                          color=color,
                          edgecolor=None)

            patch = bars[0]
            path = patch.get_path()
            trans = patch.get_transform()

            ax.add_patch(
                matplotlib.patches.PathPatch(
                    path,
                    transform=trans,
                    fill=False,
                    edgecolor=line_color,
                    linewidth=arc_linewidth
                )
            )

        # ===== 1.0(=100%) の連続区間を外縁でつなぐ =====
        i = 0
        while i < len(scores):

            if not np.isclose(scores[i], 1.0):
                i += 1
                continue

            start = i
            while i < len(scores) and np.isclose(scores[i], 1.0):
                i += 1
            end = i - 1

            theta_left = edges[start]
            theta_right = edges[end + 1]

            theta_arc = np.linspace(theta_left, theta_right, 200)
            r_arc = np.full_like(theta_arc, base + layer_height)

            ax.plot(theta_arc, r_arc,
                    color=line_color,
                    linewidth=2.0)

            ax.plot([theta_left, theta_left],
                    [base, base + layer_height],
                    color=line_color,
                    linewidth=vertical_linewidth)

            ax.plot([theta_right, theta_right],
                    [base, base + layer_height],
                    color=line_color,
                    linewidth=vertical_linewidth)

        # ===== ラベル =====
        label = label_map.get(c, c)

        ax.text(np.pi / 2,
                base + layer_height / 2,
                label,
                ha="center",
                va="center",
                fontsize=11,
                fontweight="bold")

    # ===== 中央 =====
    ax.text(np.pi / 2, 0.8,
            "個人的決定因子",
            ha="center",
            va="center",
            fontsize=11)

    ax.set_xticks(angles)
    ax.set_xticklabels(all_ages)
    ax.set_yticks([])

    # =========================================================
    # ★ 外周追加：年齢ラベルと生活段階ラベル
    # =========================================================

    outer_base = inner_blank + len(categories) * layer_height

    # =========================================================
    # ★ 項目名は「10歳の範囲開始位置」に置く
    # =========================================================
    idx_10 = np.where(all_ages == 10)[0][0]
    theta_10_start = edges[idx_10]

    # 「年齢」
    ax.text(theta_10_start,
            outer_base + 0.6,
            "年齢",
            ha="center",
            va="center",
            fontsize=10)

    # 「生活段階」
    ax.text(theta_10_start,
            outer_base + 1.4,
            "生活\n段階",
            ha="center",
            va="center",
            fontsize=10)

    # =========================================================
    # ★ 指定年齢に最も近い角度を返す関数（45や75が無くても表示できる）
    # =========================================================

    def nearest_angle(target_age):
        idx = np.argmin(np.abs(all_ages - target_age))
        return angles[idx]

    # =========================================================
    # ★ 生活段階：指定年齢に最も近い場所へ配置
    # =========================================================
    life_stage_positions = [
        ("成長", nearest_angle(10)),
        ("探索", nearest_angle(20)),
        ("確立", nearest_angle(30)),
        ("維持", nearest_angle(45)),
        ("解放", nearest_angle(75))
    ]

    for stage, theta in life_stage_positions:
        ax.text(theta,
                outer_base + 1.4,
                stage,
                ha="center",
                va="center",
                fontsize=11)

    # =========================================================

    # ===== PNG保存 =====
    plt.savefig(
        output_path,
        dpi=300,
        bbox_inches="tight"
    )

    plt.close()

    return output_path
