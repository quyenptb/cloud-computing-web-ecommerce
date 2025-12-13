# live_consumer.py
from kafka import KafkaConsumer
import json
import time
import sys

# Dùng tên service trong Docker, hoạt động khi chạy bên trong container store-backend
BOOTSTRAP_SERVERS = 'kafka:29092' 
TOPIC_NAME = 'sales_transactions'

try:
    # Khởi tạo consumer
    consumer = KafkaConsumer(
        TOPIC_NAME,
        bootstrap_servers=[BOOTSTRAP_SERVERS],
        # Đọc tin nhắn MỚI NHẤT từ lúc consumer này khởi động (live feed)
        auto_offset_reset='latest', 
        enable_auto_commit=True, 
        group_id='live-monitor-group',
        # Bỏ timeout để nó chạy liên tục
    )

    print(f"--- Đang lắng nghe tin nhắn TRONG THỜI GIAN THỰC trên topic: {TOPIC_NAME} ---")
    print("Nhấn Ctrl+C để dừng.")
    
    count = 0
    # Vòng lặp vô hạn, lắng nghe tin nhắn mới đến
    for message in consumer:
        count += 1
        decoded_message = message.value.decode('utf-8')
        print(f"#{count} @ {time.strftime('%H:%M:%S')}: {decoded_message[:150]}...")
            
except KeyboardInterrupt:
    print("\n--- Dừng consumer do người dùng ngắt (Ctrl+C). ---")
except Exception as e:
    print(f"Lỗi khi kết nối hoặc đọc tin nhắn: {e}")
    # In full traceback để debug chi tiết
    import traceback
    traceback.print_exc()
finally:
    if 'consumer' in locals() and consumer is not None:
        consumer.close()
        print("Đã đóng consumer.")
