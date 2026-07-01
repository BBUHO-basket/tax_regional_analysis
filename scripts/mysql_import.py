import math
import os
import pandas as pd
import mysql.connector
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).parent.parent
CSV_PATH = BASE_DIR / 'data' / 'processed' / 'vat_processed.csv'

load_dotenv(BASE_DIR / '.env')

DB_CONFIG = {
    'host':     os.getenv('DB_HOST', 'localhost'),
    'user':     os.getenv('DB_USER', 'root'),
    'password': os.getenv('DB_PASSWORD'),
    'port':     int(os.getenv('DB_PORT', 3306)),
}
DB_NAME = 'vat_db'
TABLE   = 'vat_report'

CREATE_DB = (
    f'CREATE DATABASE IF NOT EXISTS `{DB_NAME}`'
    ' CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci'
)

CREATE_TABLE = f"""
CREATE TABLE IF NOT EXISTS `{TABLE}` (
    id                INT AUTO_INCREMENT PRIMARY KEY,
    region            VARCHAR(20)  NOT NULL COMMENT '지역',
    industry          VARCHAR(50)  NOT NULL COMMENT '업종',
    tax_people_count  INT                   COMMENT '신고 인원',
    tax_base          BIGINT                COMMENT '과세분매출 과세표준 (백만원)',
    zero_tax_base     BIGINT                COMMENT '영세율 매출 과세표준 (백만원)',
    pay_tax           BIGINT                COMMENT '차감납부할 세액 (백만원)',
    refund_tax        BIGINT                COMMENT '차감환급할 세액 (백만원)',
    final_tax         BIGINT                COMMENT '최종 세액 = pay_tax - refund_tax (백만원)'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
"""

INSERT_SQL = f"""
INSERT INTO `{TABLE}`
    (region, industry, tax_people_count, tax_base, zero_tax_base, pay_tax, refund_tax, final_tax)
VALUES
    (%s, %s, %s, %s, %s, %s, %s, %s)
"""


def none_if_nan(val):
    if val is None:
        return None
    try:
        if math.isnan(float(val)):
            return None
        return int(val)
    except (TypeError, ValueError):
        return None


def main():
    df = pd.read_csv(CSV_PATH, encoding='utf-8-sig')

    conn = mysql.connector.connect(**DB_CONFIG)
    cur  = conn.cursor()

    cur.execute(CREATE_DB)
    cur.execute(f'USE `{DB_NAME}`')
    cur.execute(CREATE_TABLE)
    conn.commit()
    print(f'데이터베이스 [{DB_NAME}] / 테이블 [{TABLE}] 준비 완료')

    rows = [
        (
            row['region'],
            row['industry'],
            none_if_nan(row['tax_people_count']),
            none_if_nan(row['tax_base']),
            none_if_nan(row['zero_tax_base']),
            none_if_nan(row['pay_tax']),
            none_if_nan(row['refund_tax']),
            none_if_nan(row['final_tax']),
        )
        for _, row in df.iterrows()
    ]

    cur.executemany(INSERT_SQL, rows)
    conn.commit()
    print(f'{cur.rowcount}행 삽입 완료')

    cur.execute(f'SELECT COUNT(*) FROM `{TABLE}`')
    print(f'테이블 총 레코드: {cur.fetchone()[0]}행')

    cur.close()
    conn.close()


if __name__ == '__main__':
    main()
