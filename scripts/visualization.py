import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import matplotlib.patches as mpatches
import numpy as np
from pathlib import Path

plt.rcParams['font.family'] = 'Malgun Gothic'
plt.rcParams['axes.unicode_minus'] = False

BASE_DIR   = Path(__file__).parent.parent
OUTPUT_DIR = BASE_DIR / 'data' / 'output'
CHART_DIR  = BASE_DIR / 'charts'

vat  = pd.read_csv(OUTPUT_DIR / 'q2_vat_by_region.csv',            encoding='utf-8-sig')
top3 = pd.read_csv(OUTPUT_DIR / 'q3_top3_industry_by_region.csv',  encoding='utf-8-sig')
zero = pd.read_csv(OUTPUT_DIR / 'q4_zero_tax_ratio_by_region.csv', encoding='utf-8-sig')


# ── 1. 지역별 VAT 규모 — 가로 막대그래프 ────────────────────────
vat_s = vat.sort_values('최종세액_합계', ascending=True)

fig, ax = plt.subplots(figsize=(10, 7))
bars = ax.barh(
    vat_s['지역'], vat_s['최종세액_합계'] / 1e6,
    color='steelblue', edgecolor='white', height=0.6
)
for bar, val in zip(bars, vat_s['최종세액_합계']):
    ax.text(
        bar.get_width() + 0.02, bar.get_y() + bar.get_height() / 2,
        f'{val/1e6:.2f}조', va='center', fontsize=9, color='#333333'
    )
ax.set_xlabel('최종세액 (조원)', fontsize=11)
ax.set_title('지역별 VAT 규모 (최종세액 기준)', fontsize=14, fontweight='bold', pad=15)
ax.xaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f'{x:.1f}조'))
ax.set_xlim(0, vat_s['최종세액_합계'].max() / 1e6 * 1.18)
ax.spines[['top', 'right']].set_visible(False)
ax.tick_params(axis='y', labelsize=10)
ax.grid(axis='x', linestyle='--', alpha=0.4)
plt.tight_layout()
plt.savefig(CHART_DIR / 'chart1_vat_by_region.png', dpi=150, bbox_inches='tight')
plt.close()
print('저장: chart1_vat_by_region.png')


# ── 2. 지역별 TOP3 산업 — 누적 가로 막대그래프 ──────────────────
pivot = top3.pivot_table(index='지역', columns='순위', values='최종세액', aggfunc='sum')
pivot.columns = ['1위', '2위', '3위']
label_map = top3.set_index(['지역', '순위'])['업종'].to_dict()
region_order = vat.sort_values('최종세액_합계', ascending=False)['지역'].tolist()
pivot = pivot.reindex(region_order)

COLORS = ['#2C7BB6', '#ABD9E9', '#FDAE61']

fig, ax = plt.subplots(figsize=(13, 8))
lefts = np.zeros(len(pivot))
for rank_col, color, rlabel in zip(['1위', '2위', '3위'], COLORS, ['1위', '2위', '3위']):
    vals = pivot[rank_col].fillna(0).values / 1e3
    bars = ax.barh(pivot.index, vals, left=lefts, color=color,
                   label=rlabel, edgecolor='white', height=0.6)
    for i, (bar, region) in enumerate(zip(bars, pivot.index)):
        rank_num = int(rlabel[0])
        ind_name = label_map.get((region, rank_num), '')
        w = bar.get_width()
        if w > 30:
            ax.text(
                lefts[i] + w / 2, bar.get_y() + bar.get_height() / 2,
                ind_name, ha='center', va='center',
                fontsize=7.5, color='white', fontweight='bold'
            )
    lefts += vals
ax.set_xlabel('최종세액 합계 (십억원)', fontsize=11)
ax.set_title('지역별 TOP3 핵심산업 (누적 최종세액)', fontsize=14, fontweight='bold', pad=15)
ax.xaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f'{x:,.0f}B'))
ax.legend(title='순위', loc='lower right', fontsize=9)
ax.spines[['top', 'right']].set_visible(False)
ax.tick_params(axis='y', labelsize=10)
ax.grid(axis='x', linestyle='--', alpha=0.4)
plt.tight_layout()
plt.savefig(CHART_DIR / 'chart2_top3_industry.png', dpi=150, bbox_inches='tight')
plt.close()
print('저장: chart2_top3_industry.png')


# ── 3. 영세율 비중 — 가로 막대그래프 ────────────────────────────
zero_s = zero.sort_values('영세율_비중_PCT', ascending=True)
colors = ['#D73027' if v < 0 else '#4575B4' for v in zero_s['영세율_비중_PCT']]

fig, ax = plt.subplots(figsize=(10, 7))
bars = ax.barh(zero_s['지역'], zero_s['영세율_비중_PCT'], color=colors, edgecolor='white', height=0.6)
for bar, val in zip(bars, zero_s['영세율_비중_PCT']):
    x_pos = bar.get_width() + (0.05 if val >= 0 else -0.05)
    ha = 'left' if val >= 0 else 'right'
    ax.text(x_pos, bar.get_y() + bar.get_height() / 2,
            f'{val:.2f}%', va='center', ha=ha, fontsize=9, color='#333333')
ax.axvline(0, color='black', linewidth=0.8)
ax.set_xlabel('영세율 비중 (%)', fontsize=11)
ax.set_title('지역별 영세율 매출 과세표준 비중\n(음수 = 수정신고로 인한 이상값)', fontsize=13, fontweight='bold', pad=15)
ax.spines[['top', 'right']].set_visible(False)
ax.tick_params(axis='y', labelsize=10)
ax.grid(axis='x', linestyle='--', alpha=0.4)
pos_patch = mpatches.Patch(color='#4575B4', label='양수 (정상)')
neg_patch = mpatches.Patch(color='#D73027', label='음수 (수정신고 추정)')
ax.legend(handles=[pos_patch, neg_patch], fontsize=9, loc='lower right')
plt.tight_layout()
plt.savefig(CHART_DIR / 'chart3_zero_tax_ratio.png', dpi=150, bbox_inches='tight')
plt.close()
print('저장: chart3_zero_tax_ratio.png')
