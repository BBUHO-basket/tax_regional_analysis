# 분석 방법론

## 데이터 출처

- **원본 파일**: `data/raw/2025년_2기_부가가치세_신고현황.xlsx`
- **출처**: 국세청 부가가치세 신고 현황 (2025년 2기, 일반사업자)
- **단위**: 금액 항목 전체 백만원

## 분석 파이프라인

### 1단계 — 전처리 (`scripts/preprocessing.py`)

원본 xlsx 파일은 지역마다 셀 병합 방식이 달라 세 가지 포맷으로 분기 파싱합니다.

| 포맷 | 해당 지역 | 특징 |
|------|----------|------|
| A | 서울, 인천 | 업종별 개별 행, 열 위치 세트 1 |
| B | 경기 등 13개 | 줄바꿈(`\n`)으로 묶인 멀티라인 셀 |
| C | 대전, 충북 | 업종별 개별 행, 열 위치 세트 2 |

파싱 후 `final_tax = pay_tax - refund_tax` 파생 컬럼을 추가하여 `data/processed/vat_processed.csv`로 저장합니다.

### 2단계 — DB 적재 (`scripts/mysql_import.py`)

전처리된 CSV를 MySQL `vat_db.vat_report` 테이블에 적재합니다.  
테이블 스키마는 `sql/create_table.sql` 참조.

### 3단계 — 분석 (`scripts/analysis.py`)

MySQL 쿼리로 4개 분석 질문에 답하고 결과를 CSV로 저장합니다.

| 질문 | 출력 파일 |
|------|----------|
| Q1. 데이터 구성 개요 | `q1_data_overview.csv`, `q1_basic_stats.csv` |
| Q2. 지역별 VAT 규모 | `q2_vat_by_region.csv` |
| Q3. 지역별 TOP3 산업 | `q3_top3_industry_by_region.csv` |
| Q4. 지역별 영세율 비중 | `q4_zero_tax_ratio_by_region.csv` |

이후 파생 테이블을 생성합니다.

- `region_industry_summary.csv` — 지역별 TOP3 업종 피벗 + 핵심산업 특징
- `negative_zero_tax.csv` — 영세율 과세표준이 음수인 이상값 레코드
- `region_final_analysis.csv` — 위 두 테이블 병합 + 지역 경제 유형 분류

### 4단계 — 시각화

| 스크립트 | 출력 차트 |
|----------|----------|
| `scripts/visualization.py` | chart1 ~ chart3 (막대그래프) |
| `scripts/map_visualization.py` | chart4 (지역별 경제 유형 지도) |

## 영세율 비중 계산식

```
영세율_비중(%) = zero_tax_base / (tax_base + zero_tax_base) × 100
```

음수 값은 수정신고로 인한 이상값으로 별도 추출하여 관리합니다.
