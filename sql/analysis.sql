-- ============================================================
-- VAT 분석 쿼리 모음
-- DB: vat_db  /  TABLE: vat_report
-- 금액 단위: 백만원  /  MySQL 5.6 호환
-- ============================================================

USE vat_db;


-- ============================================================
-- Q1. 데이터가 무엇으로 구성되어 있는가
-- ============================================================

-- 1-1. 기본 구성 현황
SELECT
    COUNT(*)                    AS 총_레코드수,
    COUNT(DISTINCT region)      AS 지역수,
    COUNT(DISTINCT industry)    AS 업종수
FROM vat_report;

-- 1-2. 지역 목록
SELECT DISTINCT region
FROM vat_report
ORDER BY region;

-- 1-3. 업종 목록
SELECT DISTINCT industry
FROM vat_report
ORDER BY industry;

-- 1-4. 컬럼별 기초 통계 (단위: 백만원)
SELECT '신고인원'       AS 항목, MIN(tax_people_count) AS 최솟값, MAX(tax_people_count) AS 최댓값, ROUND(AVG(tax_people_count),0) AS 평균값, SUM(tax_people_count) AS 합계 FROM vat_report
UNION ALL
SELECT '과세표준',       MIN(tax_base),        MAX(tax_base),        ROUND(AVG(tax_base),0),        SUM(tax_base)        FROM vat_report
UNION ALL
SELECT '영세율과세표준', MIN(zero_tax_base),   MAX(zero_tax_base),   ROUND(AVG(zero_tax_base),0),   SUM(zero_tax_base)   FROM vat_report
UNION ALL
SELECT '납부세액',       MIN(pay_tax),         MAX(pay_tax),         ROUND(AVG(pay_tax),0),         SUM(pay_tax)         FROM vat_report
UNION ALL
SELECT '환급세액',       MIN(refund_tax),      MAX(refund_tax),      ROUND(AVG(refund_tax),0),      SUM(refund_tax)      FROM vat_report
UNION ALL
SELECT '최종세액',       MIN(final_tax),       MAX(final_tax),       ROUND(AVG(final_tax),0),       SUM(final_tax)       FROM vat_report;

-- 1-5. NULL 값 현황
SELECT
    SUM(CASE WHEN tax_people_count IS NULL THEN 1 ELSE 0 END) AS tax_people_count_null,
    SUM(CASE WHEN tax_base         IS NULL THEN 1 ELSE 0 END) AS tax_base_null,
    SUM(CASE WHEN zero_tax_base    IS NULL THEN 1 ELSE 0 END) AS zero_tax_base_null,
    SUM(CASE WHEN pay_tax          IS NULL THEN 1 ELSE 0 END) AS pay_tax_null,
    SUM(CASE WHEN refund_tax       IS NULL THEN 1 ELSE 0 END) AS refund_tax_null,
    SUM(CASE WHEN final_tax        IS NULL THEN 1 ELSE 0 END) AS final_tax_null
FROM vat_report;


-- ============================================================
-- Q2. 지역별 VAT 규모는 어떻게 다른가 (final_tax 기준)
-- ============================================================

SELECT
    a.region                                                            AS 지역,
    a.납부세액_합계,
    a.환급세액_합계,
    a.최종세액_합계,
    ROUND(a.최종세액_합계 * 100.0 / (SELECT SUM(final_tax) FROM vat_report), 2)
                                                                        AS 전국대비_비중_PCT,
    (SELECT COUNT(*) + 1
     FROM (
         SELECT region, SUM(final_tax) AS s
         FROM vat_report GROUP BY region
     ) b
     WHERE b.s > a.최종세액_합계)                                        AS 순위
FROM (
    SELECT
        region,
        SUM(pay_tax)    AS 납부세액_합계,
        SUM(refund_tax) AS 환급세액_합계,
        SUM(final_tax)  AS 최종세액_합계
    FROM vat_report
    GROUP BY region
) a
ORDER BY a.최종세액_합계 DESC;


-- ============================================================
-- Q3. 지역별 TOP 3 산업 (final_tax 기준)
-- ============================================================

SELECT
    a.region    AS 지역,
    a.industry  AS 업종,
    a.최종세액,
    (SELECT COUNT(*) + 1
     FROM (
         SELECT region, industry, SUM(final_tax) AS s
         FROM vat_report
         WHERE final_tax IS NOT NULL
         GROUP BY region, industry
     ) b
     WHERE b.region = a.region AND b.s > a.최종세액)  AS 순위
FROM (
    SELECT region, industry, SUM(final_tax) AS 최종세액
    FROM vat_report
    WHERE final_tax IS NOT NULL
    GROUP BY region, industry
) a
WHERE (
    SELECT COUNT(*)
    FROM (
        SELECT region, SUM(final_tax) AS s
        FROM vat_report
        WHERE final_tax IS NOT NULL
        GROUP BY region, industry
    ) b
    WHERE b.region = a.region AND b.s > a.최종세액
) < 3
ORDER BY a.region, a.최종세액 DESC;


-- ============================================================
-- Q4. 지역별 영세율 비중은 얼마나 다른가
--     영세율 비중 = zero_tax_base / (tax_base + zero_tax_base) * 100
-- ============================================================

SELECT
    a.region                                AS 지역,
    a.과세표준_합계,
    a.영세율과세표준_합계,
    a.과세표준_합계 + a.영세율과세표준_합계 AS 총_매출_과세표준,
    ROUND(
        a.영세율과세표준_합계 * 100.0
        / NULLIF(a.과세표준_합계 + a.영세율과세표준_합계, 0)
    , 2)                                    AS 영세율_비중_PCT,
    (SELECT COUNT(*) + 1
     FROM (
         SELECT region,
                SUM(zero_tax_base) * 100.0
                / NULLIF(SUM(tax_base) + SUM(zero_tax_base), 0) AS pct
         FROM vat_report GROUP BY region
     ) b
     WHERE b.pct > a.영세율과세표준_합계 * 100.0
                   / NULLIF(a.과세표준_합계 + a.영세율과세표준_합계, 0)
    )                                       AS 순위
FROM (
    SELECT
        region,
        SUM(tax_base)       AS 과세표준_합계,
        SUM(zero_tax_base)  AS 영세율과세표준_합계
    FROM vat_report
    GROUP BY region
) a
ORDER BY 영세율_비중_PCT DESC;
