-- ============================================================
-- 데이터 임포트
-- 실제 적재는 scripts/mysql_import.py (Python) 로 수행합니다.
-- 아래는 MySQL LOAD DATA 방식의 참조용 예시입니다.
-- ============================================================

USE vat_db;

-- CSV 직접 임포트 (mysql --local-infile=1 옵션 필요)
LOAD DATA LOCAL INFILE 'data/processed/vat_processed.csv'
INTO TABLE vat_report
CHARACTER SET utf8mb4
FIELDS TERMINATED BY ','
OPTIONALLY ENCLOSED BY '"'
LINES TERMINATED BY '\n'
IGNORE 1 ROWS
(region, industry, tax_people_count, tax_base, zero_tax_base, pay_tax, refund_tax, final_tax);
