import os
from pyflink.datastream import StreamExecutionEnvironment
from pyflink.table import StreamTableEnvironment, EnvironmentSettings

from pyflink.common import RestartStrategies
from pyflink.datastream import CheckpointingMode

def main():
    # 1. Setup môi trường Flink
    env = StreamExecutionEnvironment.get_execution_environment()
    env.set_parallelism(1)

    # --- CẤU HÌNH RESTART STRATEGY ---
    # Cấu hình Flink tự động khởi động lại 3 lần khi gặp lỗi, mỗi lần cách nhau 10 giây
    env.set_restart_strategy(RestartStrategies.fixed_delay_restart(
        restart_attempts=3,
        delay_between_attempts=10000 # tính bằng milliseconds (10 giây)
    ))

    # --- CẤU HÌNH CHECKPOINTING ---
    # Bật Checkpoint, lưu trạng thái mỗi 60 giây (60000 ms)
    env.enable_checkpointing(60000) 
    # Tùy chọn thêm: 
    # env.get_checkpointing_config().set_checkpointing_mode(CheckpointingMode.EXACTLY_ONCE)
    # env.get_checkpointing_config().set_checkpoint_timeout(60000)
    # env.get_checkpointing_config().set_max_concurrent_checkpoints(1)
    # env.get_checkpointing_config().set_min_pause_between_checkpoints(5000)


    # --- CẤU HÌNH LOAD JAR ---
    current_dir = os.path.dirname(os.path.abspath(__file__))
    jar_dir = os.path.join(current_dir, "lib")
    
    # Danh sách JAR file (đảm bảo phiên bản khớp với hướng dẫn trước)
    jar_files = [
        f"file://{os.path.join(jar_dir, 'flink-sql-connector-kafka-3.3.0-1.20.jar')}",
        f"file://{os.path.join(jar_dir, 'flink-connector-jdbc-3.3.0-1.20.jar')}",
        f"file://{os.path.join(jar_dir, 'postgresql-42.6.0.jar')}"
    ]
    
    env.add_jars(*jar_files)
    jar_str = ";".join(jar_files)
    
    settings = EnvironmentSettings.new_instance().in_streaming_mode().build()
    t_env = StreamTableEnvironment.create(env, environment_settings=settings)
    t_env.get_config().get_configuration().set_string("pipeline.jars", jar_str)
    
    print("Môi trường Flink đã sẵn sàng. Đang khởi tạo Job...")

    # 2. Định nghĩa Source (Đọc từ Kafka)
    t_env.execute_sql("""
        CREATE TABLE sales_source (
            transaction_id STRING,
            product_id STRING,
            quantity INT,
            price DOUBLE,
            `timestamp` BIGINT,
            customer_id INT,
            store_id STRING,
            ts AS TO_TIMESTAMP_LTZ(`timestamp`, 3),
            WATERMARK FOR ts AS ts - INTERVAL '5' SECOND
        ) WITH (
            'connector' = 'kafka',
            'topic' = 'sales_transactions',
            'properties.bootstrap.servers' = 'kafka:29092',
            'properties.group.id' = 'flink_retail_group',
            'scan.startup.mode' = 'latest-offset',
            'format' = 'json',
            'json.ignore-parse-errors' = 'true'
        )
    """)

    # 3. Định nghĩa 3 Sink (Ghi vào 3 bảng Postgres)
    
    # Sink 1: Doanh thu theo Sản phẩm
    t_env.execute_sql("""
        CREATE TABLE product_sales_sink (
            window_start TIMESTAMP(3),
            window_end TIMESTAMP(3),
            product_id STRING,
            total_revenue DOUBLE,
            total_quantity BIGINT,
            PRIMARY KEY (window_start, window_end, product_id) NOT ENFORCED
        ) WITH (
            'connector' = 'jdbc',
            'url' = 'jdbc:postgresql://postgres:5432/retail_analytics',
            'table-name' = 'product_sales',
            'username' = 'admin',
            'password' = 'password'
        )
    """)

    # Sink 2: Tổng doanh thu toàn hệ thống
    t_env.execute_sql("""
        CREATE TABLE total_sales_sink (
            window_start TIMESTAMP(3),
            window_end TIMESTAMP(3),
            grand_total_revenue DOUBLE PRECISION,
            grand_total_orders BIGINT,
            PRIMARY KEY (window_start, window_end) NOT ENFORCED
        ) WITH (
            'connector' = 'jdbc',
            'url' = 'jdbc:postgresql://postgres:5432/retail_analytics',
            'table-name' = 'total_sales',
            'username' = 'admin',
            'password' = 'password'
        )
    """)

    # Sink 3: Doanh thu theo Cửa hàng
    t_env.execute_sql("""
        CREATE TABLE store_sales_sink (
            window_start TIMESTAMP(3),
            window_end TIMESTAMP(3),
            store_id STRING,
            store_revenue DOUBLE,
            PRIMARY KEY (window_start, window_end, store_id) NOT ENFORCED
        ) WITH (
            'connector' = 'jdbc',
            'url' = 'jdbc:postgresql://postgres:5432/retail_analytics',
            'table-name' = 'store_sales',
            'username' = 'admin',
            'password' = 'password'
        )
    """)

    # 4. Xử lý và Ghi dữ liệu (Dùng StatementSet để chạy nhiều query cùng lúc)
    statement_set = t_env.create_statement_set()

    # Query 1: Tính theo Sản phẩm
    statement_set.add_insert_sql("""
        INSERT INTO product_sales_sink
        SELECT
            window_start,
            window_end,
            product_id,
            SUM(quantity * price) AS total_revenue,
            SUM(quantity) AS total_quantity
        FROM TABLE(
            TUMBLE(TABLE sales_source, DESCRIPTOR(ts), INTERVAL '1' MINUTE)
        )
        GROUP BY window_start, window_end, product_id
    """)

    # Query 2: Tính Tổng toàn cục
    statement_set.add_insert_sql("""
        INSERT INTO total_sales_sink
        SELECT
            window_start,
            window_end,
            SUM(quantity * price) AS grand_total_revenue,
            COUNT(transaction_id) AS grand_total_orders
        FROM TABLE(
            TUMBLE(TABLE sales_source, DESCRIPTOR(ts), INTERVAL '1' MINUTE)
        )
        GROUP BY window_start, window_end
    """)

    # Query 3: Tính theo Cửa hàng
    statement_set.add_insert_sql("""
        INSERT INTO store_sales_sink
        SELECT
            window_start,
            window_end,
            store_id, 
            SUM(quantity * price) AS store_revenue
        FROM TABLE(
            TUMBLE(TABLE sales_source, DESCRIPTOR(ts), INTERVAL '1' MINUTE)
        )
        GROUP BY window_start, window_end, store_id 
    """)

    print("Đang chạy Job Flink... Đang lắng nghe Kafka...")
    result = statement_set.execute()
    
    # Quan trọng: Chờ job chạy để process không bị kill
    result.wait()

if __name__ == '__main__':
    main()