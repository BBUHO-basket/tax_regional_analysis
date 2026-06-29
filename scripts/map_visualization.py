import json
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import Polygon as MplPolygon
from pathlib import Path

plt.rcParams['font.family'] = 'Malgun Gothic'
plt.rcParams['axes.unicode_minus'] = False

BASE_DIR = Path(__file__).parent.parent
GEO_PATH = r'C:\Users\USER\AppData\Local\Temp\korea_provinces.json'
CSV_PATH = BASE_DIR / 'data' / 'output' / 'region_final_analysis.csv'
OUT_PATH = BASE_DIR / 'charts' / 'chart4_korea_map.png'

NAME_MAP = {
    '서울특별시': '서울', '부산광역시': '부산', '대구광역시': '대구',
    '인천광역시': '인천', '광주광역시': '광주', '대전광역시': '대전',
    '울산광역시': '울산', '세종특별자치시': '세종', '경기도': '경기',
    '강원도': '강원', '충청북도': '충북', '충청남도': '충남',
    '전라북도': '전북', '전라남도': '전남', '경상북도': '경북',
    '경상남도': '경남', '제주특별자치도': '제주',
}

TYPE_COLORS = {
    '소비·서비스형': '#4575B4',
    '생산형':        '#74C476',
    '수출·물류형':   '#FD8D3C',
    '중공업 제조형': '#D73027',
    '행정·개발형':   '#9E9AC8',
}

LABEL_OFFSET = {
    '경기': (0.0, -0.25), '강원': (0.25, 0.0),
    '충남': (-0.15, 0.0), '충북': (0.05, 0.15),
    '대전': (0.0, -0.05), '세종': (-0.05, 0.0),
    '전북': (0.0,  0.1),  '경북': (0.0,  0.1),
}

df = pd.read_csv(CSV_PATH, encoding='utf-8-sig')
type_map = df.set_index('지역')['유형'].to_dict()

with open(GEO_PATH, encoding='utf-8') as f:
    geo = json.load(f)

fig, ax = plt.subplots(figsize=(10, 13), facecolor='#F0F4F8')
ax.set_facecolor('#D6E8F5')

for feat in geo['features']:
    geo_name = feat['properties']['name']
    region   = NAME_MAP.get(geo_name, geo_name)
    rtype    = type_map.get(region, '')
    color    = TYPE_COLORS.get(rtype, '#CCCCCC')
    geom     = feat['geometry']

    polys_coords = []
    if geom['type'] == 'Polygon':
        polys_coords = [geom['coordinates'][0]]
    elif geom['type'] == 'MultiPolygon':
        polys_coords = [p[0] for p in geom['coordinates']]

    all_xy = []
    for ring in polys_coords:
        xy = np.array(ring)
        patch = MplPolygon(xy, closed=True,
                           facecolor=color, edgecolor='white',
                           linewidth=0.9, zorder=2)
        ax.add_patch(patch)
        all_xy.append(xy)

    if all_xy:
        largest = max(all_xy, key=lambda a: len(a))
        cx = np.mean(largest[:, 0])
        cy = np.mean(largest[:, 1])
        dx, dy = LABEL_OFFSET.get(region, (0, 0))
        ax.text(cx + dx, cy + dy, region,
                ha='center', va='center',
                fontsize=8.5, fontweight='bold', color='white', zorder=4,
                bbox=dict(boxstyle='round,pad=0.15',
                          facecolor=color, edgecolor='none', alpha=0.7))

legend_handles = [
    mpatches.Patch(facecolor=c, edgecolor='#555', label=t)
    for t, c in TYPE_COLORS.items()
]
legend = ax.legend(
    handles=legend_handles,
    title='■ 지역 경제 유형',
    title_fontsize=10,
    fontsize=9.5,
    loc='lower left',
    framealpha=0.95,
    edgecolor='#AAAAAA',
    borderpad=1.0,
)
legend.get_title().set_fontweight('bold')

ax.set_xlim(125.5, 130.1)
ax.set_ylim(33.0, 38.7)
ax.set_aspect('equal')
ax.axis('off')
ax.set_title('대한민국 지역별 경제 유형 분류\n(부가가치세 신고 데이터 기반, 2025년 2기)',
             fontsize=13, fontweight='bold', pad=18, color='#222222')

plt.tight_layout()
plt.savefig(OUT_PATH, dpi=150, bbox_inches='tight', facecolor='#F0F4F8')
plt.close()
print(f'저장 완료: {OUT_PATH}')
