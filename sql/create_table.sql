-- ============================================================
-- DB 및 테이블 생성
-- DB: vat_db  /  TABLE: vat_report
-- 금액 단위: 백만원  /  MySQL 5.6 호환
-- ============================================================

CREATE DATABASE IF NOT EXISTS `vat_db`
    CHARACTER SET utf8mb4
    COLLATE utf8mb4_unicode_ci;

USE vat_db;

CREATE TABLE IF NOT EXISTS `vat_report` (
    id                INT AUTO_INCREMENT PRIMARY KEY,
    region            VARCHAR(20)  NOT NULL COMMENT '지역',
    industry          VARCHAR(50)  NOT NULL COMMENT '업종',
    tax_people_count  INT                   COMMENT '신고 인원',
    tax_base          BIGINT                COMMENT '과세분매출 과세표준 (백만원)',
    zero_tax_base     BIGINT                COMMENT '영세율 매출 과세표준 (백만원)',
    pay_tax           BIGINT                COMMENT '차감납부할 세액 (백만원)',
    refund_tax        BIGINT                COMMENT '차감환급할 세액 (백만원)',
    final_tax         BIGINT                COMMENT '최종 세액 = pay_tax - refund_tax (백만원)'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
