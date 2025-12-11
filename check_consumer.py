from kafka import KafkaConsumer
import json
import time

BOOTSTRAP_SERVERS = 'kafka:29092' 
TOPIC_NAME = 'sales_transactions'

try:
    # Khởi tạo consumer
    consumer = KafkaConsumer(
        TOPIC_NAME,
        bootstrap_servers=[BOOTSTRAP_SERVERS],
        # auto_offset_reset='earliest', # Bỏ dòng này nếu chỉ muốn đọc tin nhắn mới từ lúc chạy
        enable_auto_commit=True, # Bật auto commit cho đơn giản
        group_id='test-consumer-group-long-run'
    )

    print(f"Đang lắng nghe tin nhắn liên tục trên topic: {TOPIC_NAME} tại {BOOTSTRAP_SERVERS}...")
    
    # Vòng lặp vô hạn
    for message in consumer:
        print(f"Nhận được tin nhắn: {message.value.decode('utf-8')}")
            
except KeyboardInterrupt:
    print("Dừng consumer do người dùng ngắt (Ctrl+C).")
except Exception as e:
    print(f"Lỗi khi kết nối hoặc đọc tin nhắn: {e}")
finally:
    if 'consumer' in locals() and consumer is not None:
        consumer.close()
        print("Đã đóng consumer.")

