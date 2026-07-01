"""
분석 파이프라인
  1. Q1~Q4 MySQL 쿼리 결과 CSV 저장
  2. 지역별 TOP3 산업 요약표 생성
  3. 음수 영세율 레코드 추출
  4. 지역 산업 요약 + 영세율 비중 병합 → 최종 분석 테이블
"""
import os
import mysql.connector
import pandas as pd
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR   = Path(__file__).parent.parent
OUTPUT_DIR = BASE_DIR / 'data' / 'output'
PROC_DIR   = BASE_DIR / 'data' / 'processed'

load_dotenv(BASE_DIR / '.env')

DB_CONFIG = {
    'host':     os.getenv('DB_HOST', 'localhost'),
    'user':     os.getenv('DB_USER', 'root'),
    'password': os.getenv('DB_PASSWORD'),
    'port':     int(os.getenv('DB_PORT', 3306)),
    'database': os.getenv('DB_NAME', 'vat_db'),
}

QUERIES = {
    'q1_data_overview': """
        SELECT
            COUNT(*)                 AS 총_레코드수,
            COUNT(DISTINCT region)   AS 지역수,
            COUNT(DISTINCT industry) AS 업종수
        FROM vat_report
    """,
    'q1_basic_stats': """
        SELECT '신고인원'       AS 항목, MIN(tax_people_count) AS 최솟값, MAX(tax_people_count) AS 최댓값, ROUND(AVG(tax_people_count),0) AS 평균값, SUM(tax_people_count) AS 합계 FROM vat_report
        UNION ALL SELECT '과세표준',       MIN(tax_base),        MAX(tax_base),        ROUND(AVG(tax_base),0),        SUM(tax_base)        FROM vat_report
        UNION ALL SELECT '영세율과세표준', MIN(zero_tax_base),   MAX(zero_tax_base),   ROUND(AVG(zero_tax_base),0),   SUM(zero_tax_base)   FROM vat_report
        UNION ALL SELECT '납부세액',       MIN(pay_tax),         MAX(pay_tax),         ROUND(AVG(pay_tax),0),         SUM(pay_tax)         FROM vat_report
        UNION ALL SELECT '환급세액',       MIN(refund_tax),      MAX(refund_tax),      ROUND(AVG(refund_tax),0),      SUM(refund_tax)      FROM vat_report
        UNION ALL SELECT '최종세액',       MIN(final_tax),       MAX(final_tax),       ROUND(AVG(final_tax),0),       SUM(final_tax)       FROM vat_report
    """,
    'q2_vat_by_region': """
        WITH base AS (
            SELECT
                region,
                SUM(pay_tax)    AS 납부세액_합계,
                SUM(refund_tax) AS 환급세액_합계,
                SUM(final_tax)  AS 최종세액_합계
            FROM vat_report
            GROUP BY region
        )
        SELECT
            region                                                         AS 지역,
            납부세액_합계,
            환급세액_합계,
            최종세액_합계,
            ROUND(최종세액_합계 * 100.0 / SUM(최종세액_합계) OVER (), 2) AS 전국대비_비중_PCT,
            RANK() OVER (ORDER BY 최종세액_합계 DESC)                     AS 순위
        FROM base
        ORDER BY 최종세액_합계 DESC
    """,
    'q3_top3_industry_by_region': """
        WITH ranked AS (
            SELECT
                region   AS 지역,
                industry AS 업종,
                SUM(final_tax) AS 최종세액,
                RANK() OVER (PARTITION BY region ORDER BY SUM(final_tax) DESC) AS 순위
            FROM vat_report
            WHERE final_tax IS NOT NULL
            GROUP BY region, industry
        )
        SELECT 지역, 업종, 최종세액, 순위
        FROM ranked
        WHERE 순위 <= 3
        ORDER BY 지역, 최종세액 DESC
    """,
    'q4_zero_tax_ratio_by_region': """
        WITH base AS (
            SELECT
                region,
                SUM(tax_base)      AS 과세표준_합계,
                SUM(zero_tax_base) AS 영세율과세표준_합계,
                SUM(tax_base) + SUM(zero_tax_base) AS 총_매출_과세표준,
                ROUND(
                    SUM(zero_tax_base) * 100.0
                    / NULLIF(SUM(tax_base) + SUM(zero_tax_base), 0)
                , 2) AS 영세율_비중_PCT
            FROM vat_report
            GROUP BY region
        )
        SELECT
            region             AS 지역,
            과세표준_합계,
            영세율과세표준_합계,
            총_매출_과세표준,
            영세율_비중_PCT,
            RANK() OVER (ORDER BY 영세율_비중_PCT DESC) AS 순위
        FROM base
        ORDER BY 영세율_비중_PCT DESC
    """,
}

CHARACTERISTICS = {
    '강원': '제조업 부재. 음식·서비스·건설 중심의 관광형 경제. 리조트·레저 개발이 건설 수요 견인.',
    '경기': '제조업이 전국 최대 규모로 압도적 1위. 수도권 인구 집중으로 음식업도 대규모. 부동산 임대 규모도 전국 상위권인 수도권 복합 경제권.',
    '경남': '창원·거제 중심의 중공업·조선 제조업이 압도적 1위. 전형적인 제조 산업도시 구조.',
    '경북': '포항(철강)·구미(전자) 등 공업도시 기반의 제조업 1위. 건설이 2위로 제조·인프라 복합형.',
    '광주': '음식업이 1위로 제조업보다 서비스·소비 비중이 높음. 광역시 특성의 도시형 소비 경제.',
    '대구': '전기·가스·수도업이 1위(대규모 유틸리티 사업자 VAT). 대리중개·건설이 상위권으로 부동산·서비스 중심 경제로 전환 중.',
    '대전': '제조업 없이 음식·서비스·건설이 상위권. 대덕연구개발특구 및 행정도시 성격의 서비스·지식 기반 경제.',
    '부산': '조선·항만 관련 제조업 1위. 전국 2위 항구도시답게 기타서비스(물류·해운)도 상위권.',
    '서울': '기타서비스(금융·IT 등)·부동산 임대가 1·2위 접전. 제조업 부재, 전국 최대 서비스·금융·부동산 중심지.',
    '세종': '신도시 개발로 건설이 1위. 행정중심복합도시 특성으로 건설·중개·물류가 상위권. 전체 규모는 전국 최소.',
    '울산': '현대차·현대중공업 등 대기업 기반의 제조업 절대 1위. 전국 최고 수준의 제조업 집중도.',
    '인천': '공항·항만 배후 제조업 1위. 물류·서비스(기타서비스)도 상위권인 수출입 거점 복합 구조.',
    '전남': '여수·광양 항만 물류(운수창고통신)가 3위. 음식·건설이 상위권으로 농어촌 기반 서비스형 경제.',
    '전북': '음식·건설·서비스 중심. 제조업 미진입으로 농업 기반 지역의 내수 서비스 의존 구조.',
    '제주': '관광 개발 수요로 건설이 1위. 부동산 중개·임대가 2·3위로 관광지 부동산 집중 구조.',
    '충남': '삼성(천안·아산)·현대제철(당진) 등 전자·철강 제조업 1위. 수도권 인접 제조 클러스터.',
    '충북': 'SK하이닉스(청주) 등 반도체 중심의 제조업 1위. 제조·음식·건설이 비교적 균등한 복합 구조.',
}

REGION_TYPE = {
    '서울': '소비·서비스형', '부산': '중공업 제조형', '대구': '소비·서비스형',
    '인천': '수출·물류형',  '광주': '소비·서비스형', '대전': '소비·서비스형',
    '울산': '중공업 제조형', '세종': '행정·개발형',  '경기': '생산형',
    '강원': '소비·서비스형', '충북': '생산형',       '충남': '생산형',
    '전북': '소비·서비스형', '전남': '생산형',       '경북': '생산형',
    '경남': '중공업 제조형', '제주': '소비·서비스형',
}


def run_queries(conn):
    for filename, sql in QUERIES.items():
        df = pd.read_sql(sql, conn)
        path = OUTPUT_DIR / f'{filename}.csv'
        df.to_csv(path, index=False, encoding='utf-8-sig')
        print(f'저장 완료: {filename}.csv  ({len(df)}행)')


def build_region_industry_summary():
    df = pd.read_csv(OUTPUT_DIR / 'q3_top3_industry_by_region.csv', encoding='utf-8-sig')

    pivot = (
        df.sort_values('순위')
          .groupby('지역')
          .apply(lambda g: pd.Series({
              '1위_업종':      g.iloc[0]['업종'],
              '1위_최종세액':  int(g.iloc[0]['최종세액']),
              '2위_업종':      g.iloc[1]['업종'],
              '2위_최종세액':  int(g.iloc[1]['최종세액']),
              '3위_업종':      g.iloc[2]['업종'],
              '3위_최종세액':  int(g.iloc[2]['최종세액']),
          }))
          .reset_index()
    )
    pivot['핵심산업특징'] = pivot['지역'].map(CHARACTERISTICS)

    out = OUTPUT_DIR / 'region_industry_summary.csv'
    pivot.to_csv(out, index=False, encoding='utf-8-sig')
    print(f'저장 완료: region_industry_summary.csv  ({len(pivot)}개 지역)')


def extract_negative_zero_tax():
    df = pd.read_csv(PROC_DIR / 'vat_processed.csv', encoding='utf-8-sig')

    neg = (
        df[df['zero_tax_base'] < 0]
        [['region', 'industry', 'tax_people_count', 'tax_base',
          'zero_tax_base', 'pay_tax', 'refund_tax', 'final_tax']]
        .copy()
        .sort_values('zero_tax_base')
        .reset_index(drop=True)
    )
    neg.index += 1
    neg.index.name = '순번'
    neg.columns = ['지역', '업종', '신고인원', '과세표준', '영세율과세표준', '납부세액', '환급세액', '최종세액']

    def classify(val):
        v = abs(val)
        if v >= 100_000: return '대규모 (10조원 이상 추정 수정신고)'
        if v >= 10_000:  return '중규모 (1조원 이상 추정 수정신고)'
        if v >= 1_000:   return '소규모 (1천억원 이상 추정 수정신고)'
        return '경미 (1천억원 미만)'

    neg['규모분류'] = neg['영세율과세표준'].apply(classify)

    out = OUTPUT_DIR / 'negative_zero_tax.csv'
    neg.to_csv(out, encoding='utf-8-sig')
    print(f'저장 완료: negative_zero_tax.csv  ({len(neg)}건)')


def merge_final_analysis():
    summary = pd.read_csv(
        OUTPUT_DIR / 'region_industry_summary.csv', encoding='utf-8-sig'
    ).rename(columns={'Unnamed: 7': '핵심산업특징'})

    zero = pd.read_csv(
        OUTPUT_DIR / 'q4_zero_tax_ratio_by_region.csv', encoding='utf-8-sig'
    )[['지역', '과세표준_합계', '영세율과세표준_합계', '총_매출_과세표준', '영세율_비중_PCT']]

    merged = (
        summary
        .merge(zero, on='지역', how='left')
        .sort_values('영세율_비중_PCT', ascending=False)
        .reset_index(drop=True)
    )
    merged.index += 1
    merged.index.name = '영세율_순위'
    merged['유형'] = merged['지역'].map(REGION_TYPE)

    out = OUTPUT_DIR / 'region_final_analysis.csv'
    merged.to_csv(out, encoding='utf-8-sig')
    print(f'저장 완료: region_final_analysis.csv  ({len(merged)}개 지역)')


def main():
    conn = mysql.connector.connect(**DB_CONFIG)
    try:
        run_queries(conn)
    finally:
        conn.close()

    build_region_industry_summary()
    extract_negative_zero_tax()
    merge_final_analysis()


if __name__ == '__main__':
    main()
