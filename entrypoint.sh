#!/bin/bash

# Dừng script nếu có lỗi
set -e

echo "Running 12-Factor App Entrypoint..."

# 1. Collect Static files (Gom file CSS/JS/Images về STATIC_ROOT để serve)
echo "Collecting static files..."
python manage.py collectstatic --noinput

# 2. Apply Migrations (Cập nhật cấu trúc DB)
# Lưu ý: Với Oracle, hãy chắc chắn DB đã active trước khi chạy lệnh này
echo "Applying database migrations..."
python manage.py migrate

# 3. Start Server
# Sử dụng Gunicorn cho môi trường Production thay vì runserver
echo "Starting Gunicorn Server..."
exec gunicorn store_dj.wsgi:application \
    --name store_dj \
    --bind 0.0.0.0:8000 \
    --workers 3 \
    --log-level=info \
    --access-logfile=- \
    --error-logfile=-