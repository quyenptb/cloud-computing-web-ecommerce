import os
from pyflink.datastream import StreamExecutionEnvironment
from pyflink.table import StreamTableEnvironment, EnvironmentSettings

#Flink SQL qua Table API để đọc từ Kafka và ghi vào Postgres

def main():
    # 1. Setup môi trường Flink
    env = StreamExecutionEnvironment.get_execution_environment()
    env.set_parallelism(1)
    
    # --- CẤU HÌNH LOAD JAR ---
    current_dir = os.path.dirname(os.path.abspath(__file__))
    jar_dir = os.path.join(current_dir, "lib")
    
    # Tên file đã cập nhật đúng version trên máy bạn
    jar_files = [
        f"file://{os.path.join(jar_dir, 'flink-sql-connector-kafka-3.3.0-1.20.jar')}",
        f"file://{os.path.join(jar_dir, 'flink-connector-jdbc-3.3.0-1.20.jar')}",
        f"file://{os.path.join(jar_dir, 'postgresql-42.6.0.jar')}"
    ]
    
    # 1. Nạp cho Runtime (Job chạy)
    env.add_jars(*jar_files)
    
    # 2. Nạp cho Validator (Lúc compile SQL)
    # Lưu ý: pipeline.jars dùng đường dẫn file hệ thống, ta thử dùng chuỗi jar_files này
    jar_str = ";".join(jar_files)
    
    settings = EnvironmentSettings.new_instance().in_streaming_mode().build()
    t_env = StreamTableEnvironment.create(env, environment_settings=settings)
    
    # Ép cấu hình pipeline.jars trực tiếp vào Table Environment
    t_env.get_config().get_configuration().set_string("pipeline.jars", jar_str)
    
    print(f"Đã nạp các file JAR: {jar_files}")
    # ----------------------------------

    # 2. Định nghĩa Source (Đọc từ Kafka)
    t_env.execute_sql("""
        CREATE TABLE sales_source (
            transaction_id STRING,
            product_id STRING,
            quantity INT,
            price DOUBLE,
            `timestamp` BIGINT,
            customer_id INT,
            ts AS TO_TIMESTAMP_LTZ(`timestamp`, 3),
            WATERMARK FOR ts AS ts - INTERVAL '5' SECOND
        ) WITH (
            'connector' = 'kafka',
            'topic' = 'sales_transactions',
            'properties.bootstrap.servers' = 'localhost:9092',
            'properties.group.id' = 'flink_retail_group',
            'scan.startup.mode' = 'latest-offset',
            'format' = 'json'
        )
    """)

    # 3. Định nghĩa Sink (Ghi vào Postgres)
    t_env.execute_sql("""
        CREATE TABLE sales_report_sink (
            window_start TIMESTAMP(3),
            window_end TIMESTAMP(3),
            product_id STRING,
            total_revenue DOUBLE,
            total_orders BIGINT,
            PRIMARY KEY (window_start, window_end, product_id) NOT ENFORCED
        ) WITH (
            'connector' = 'jdbc',
            'url' = 'jdbc:postgresql://localhost:5432/retail_analytics',
            'table-name' = 'sales_report',
            'username' = 'admin',
            'password' = 'password'
        )
    """)

    # 4. Thực hiện tính toán (Aggregation)
    print("Flink Job Started... Listening to Kafka...")
    
    result = t_env.execute_sql("""
        INSERT INTO sales_report_sink
        SELECT
            window_start,
            window_end,
            product_id,
            SUM(quantity * price) AS total_revenue,
            COUNT(transaction_id) AS total_orders
        FROM TABLE(
            TUMBLE(TABLE sales_source, DESCRIPTOR(ts), INTERVAL '1' MINUTE)
        )
        GROUP BY window_start, window_end, product_id
    """)
    result.wait()

if __name__ == '__main__':
    main()