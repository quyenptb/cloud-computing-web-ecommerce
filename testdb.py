import cx_Oracle

from django.db import connection
# utils.py
import openpyxl
from openpyxl.workbook import Workbook


# Khởi tạo Oracle Client
cx_Oracle.init_oracle_client(lib_dir=r"C:\Users\DungManh Laptop\Downloads\instantclient-basic-windows.x64-21.13.0.0.0dbru\instantclient_21_13")

# Cấu hình chuỗi kết nối trực tiếp
dsn = cx_Oracle.makedsn("localhost", 1521, service_name="orcl")

# Kết nối với cơ sở dữ liệu
conn = cx_Oracle.connect(user="c##django", password="django", dsn=dsn)


def call_stored_procedure():
    try:

        cursor = conn.cursor()
        
        # Thực hiện stored procedure
        result_cursor = cursor.var(cx_Oracle.CURSOR)
        cursor.callproc("get_shipping_addresses", [result_cursor])
        
        # Lấy dữ liệu từ result_cursor
        results = result_cursor.getvalue().fetchall()
        print(results)
        return results
    finally:
        cursor.close()



def generate_report(data):
    # Tạo workbook và worksheet
    wb = Workbook()
    ws = wb.active
    ws.title = "Shipping Addresses Report"

    # Thêm tiêu đề cột
    columns = ['Customer', 'Order', 'Address', 'City', 'State', 'Zipcode', 'Date Added']
    ws.append(columns)

    # Thêm dữ liệu từ stored procedure vào báo cáo
    for row in data:
        ws.append(row)  # Giả sử dữ liệu trả về là list of tuples

    return wb



results = call_stored_procedure()
print(results)

# Gọi hàm generate_report
wb = generate_report(results)

# Lưu workbook vào file
wb.save('test_report.xlsx')
