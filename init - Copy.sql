-- For Flink realtime (Flink sẽ ghi vào đây)
CREATE TABLE IF NOT EXISTS sales_report (
    window_start TIMESTAMP,
    window_end TIMESTAMP,
    product_id VARCHAR(50),
    total_revenue DOUBLE PRECISION,
    total_orders INT,
    PRIMARY KEY (window_start, window_end, product_id)
);

-- For Kafka Connector (nếu dùng CDC sau này) hoặc debug
CREATE TABLE IF NOT EXISTS sales_transactions (
    transaction_id VARCHAR(50) PRIMARY KEY,
    product_id VARCHAR(50),
    quantity INT,
    price DOUBLE PRECISION,
    customer_id INT,
    transaction_time TIMESTAMP
);