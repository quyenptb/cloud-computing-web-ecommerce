# Sử dụng Python Slim để nhẹ hơn
FROM python:3.9-slim-bullseye

# --- VARIABLES ---
# BỎ CÁC BIẾN TORCH KHÔNG CẦN THIẾT

# Environment flags
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
# Oracle Environment Variables
ENV LD_LIBRARY_PATH=/opt/oracle/instantclient_21_13:$LD_LIBRARY_PATH
ENV PATH=$PATH:/opt/oracle/instantclient_21_13


ENV PYTHONPATH=$PYTHONPATH:. 


# Working directory
WORKDIR /app

# 1. CÀI ĐẶT SYSTEM DEPENDENCIES
# libaio1 là bắt buộc cho Oracle Client
RUN apt-get update -y && \
    apt-get install -y --no-install-recommends libaio1 wget unzip gcc libpq-dev && \
    rm -rf /var/lib/apt/lists/*

# 2. ORACLE CLIENT
WORKDIR /opt/oracle
RUN wget -q https://download.oracle.com/otn_software/linux/instantclient/2113000/instantclient-basic-linux.x64-21.13.0.0.0dbru.zip \
    && unzip -q instantclient-basic-linux.x64-21.13.0.0.0dbru.zip \
    && rm instantclient-basic-linux.x64-21.13.0.0.0dbru.zip \
    && sh -c "echo /opt/oracle/instantclient_21_13 > /etc/ld.so.conf.d/oracle-instantclient.conf" \
    && ldconfig

# 3. CÀI PACKAGES (Bỏ bước cài Torch riêng)
WORKDIR /app
COPY requirements.txt /app/
RUN pip install --upgrade pip && \
    pip install -r requirements.txt && \
    pip install gunicorn whitenoise

# 4. COPY SOURCE CODE
COPY . /app/

# 5. ENTRYPOINT
RUN chmod +x /app/entrypoint.sh

EXPOSE 8000
ENTRYPOINT ["sh", "/app/entrypoint.sh"]
