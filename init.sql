-- 1. Bảng Doanh thu theo Sản phẩm (Product Sales)
CREATE TABLE product_sales (
    window_start TIMESTAMP,
    window_end TIMESTAMP,
    product_id VARCHAR(50),
    total_revenue DOUBLE PRECISION,
    total_quantity BIGINT,
    PRIMARY KEY (window_start, window_end, product_id)
);

-- 2. Bảng Tổng doanh thu toàn hệ thống (Total Revenue)
CREATE TABLE total_sales (
    window_start TIMESTAMP,
    window_end TIMESTAMP,
    grand_total_revenue DOUBLE PRECISION,
    grand_total_orders BIGINT,
    PRIMARY KEY (window_start, window_end)
);

-- 3. Bảng Doanh thu theo Cửa hàng (Store Sales)
-- Vì dữ liệu Kafka hiện tại chưa có store_id, ta sẽ giả lập 'Main_Store'
CREATE TABLE store_sales (
    window_start TIMESTAMP,
    window_end TIMESTAMP,
    store_id VARCHAR(50),
    store_revenue DOUBLE PRECISION,
    PRIMARY KEY (window_start, window_end, store_id)
);

CREATE DATABASE metabase_db;