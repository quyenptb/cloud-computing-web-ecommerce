-- 1. Kiểm tra doanh thu từng sản phẩm
SELECT * FROM product_sales ORDER BY window_start DESC;

-- 2. Kiểm tra tổng doanh thu toàn hệ thống
SELECT * FROM total_sales ORDER BY window_start DESC;

-- 3. Kiểm tra doanh thu cửa hàng
SELECT * FROM store_sales ORDER BY window_start DESC;