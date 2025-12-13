//k6 script 
import http from 'k6/http';
import { check, sleep, group } from 'k6';
import { SharedArray } from 'k6/data';

// CẤU HÌNH LOAD TEST
export const options = {
  // Chạy giai đoạn (Ramping VUs)
  scenarios: {
    stress_test: {
      executor: 'ramping-vus',
      startVUs: 0,
      stages: [
        { duration: '30s', target: 20 },  // Khởi động nhẹ
        { duration: '5m', target: 50 },  // Tăng tốc lên 100 người dùng ảo
        { duration: '10m', target: 100 }, // Stress mạnh
        { duration: '30s', target: 0 },   // Hạ nhiệt
      ],
      gracefulStop: '30s',
    },
  },
  // Lưu kết quả ra file JSON để có thông số
  // Khi chạy lệnh sẽ thêm flag --out json=results.json
};

// CẤU HÌNH MÔI TRƯỜNG (Dùng tên service trong Docker)
const BASE_URL = 'http://store-backend:8000'; 

// THÔNG TIN USER & SẢN PHẨM
const USERNAME = 'bichquyen';       
const PASSWORD = '123';
const PRODUCT_ID = 1;           // ID sản phẩm Quần jeans Trung Quốc
const PRODUCT_PRICE = 5000;    // GIÁ 5000

// Hàm lấy CSRF Token
function getCookie(name, res) {
  if (!res.cookies[name]) return null;
  return res.cookies[name][0].value;
}

export default function () {
  const jar = http.cookieJar();

  // 1. LOGIN
  group('Login Flow', function () {
    let res = http.get(`${BASE_URL}/login/`);
    let csrfToken = getCookie('csrftoken', res);

    res = http.post(`${BASE_URL}/login/`, {
      username: USERNAME,
      password: PASSWORD,
      csrfmiddlewaretoken: csrfToken,
    }, {
      headers: { 
        'Content-Type': 'application/x-www-form-urlencoded',
        'Referer': `${BASE_URL}/login/` 
      },
    });

if (res.status !== 200 && res.status !== 302) {
        console.log(`LOGIN FAILED! Status: ${res.status}, Body: ${res.body}`);
    }

    check(res, {
      'Login Success': (r) => r.status === 200 || r.status === 302,
    });
  });

  // 2. ADD ITEM TO CART (Vòng lặp để 1 người mua nhiều lần -> Kafka nhiều data)
  group('Add to Cart', function () {
    let res = http.get(`${BASE_URL}/`);
    let csrfToken = getCookie('csrftoken', res);

    let payload = JSON.stringify({
      productId: PRODUCT_ID,
      action: 'add'
    });

    let headers = {
      'Content-Type': 'application/json',
      'X-CSRFToken': csrfToken,
    };

    // Spam thêm 5 lần vào giỏ (số lượng tăng lên 5)
    for(let i = 0; i < 20; i++){
        let addRes = http.post(`${BASE_URL}/update_item/`, payload, { headers: headers });
        check(addRes, { 'Added Item': (r) => r.status === 200 });
    }
  });

  // 3. CHECKOUT (Gửi đơn hàng -> Trigger Kafka)
  group('Checkout & Kafka Trigger', function () {
    let csrfToken = getCookie('csrftoken', http.get(`${BASE_URL}/checkout/`));
    
    // Tổng tiền = Giá * Số lượng (ở trên loop 20 lần)
    let totalMoney = PRODUCT_PRICE * 20; 

    let payload = JSON.stringify({
      form: {
        name: 'bichquyen',
        email: 'phanquyenbtx@gmail.com',
        total: totalMoney.toString() // Quan trọng: Phải khớp để Django cho qua
      },
      shipping: {
        address: 'Ec2 Docker Street',
        city: 'Ha Noi',
        state: 'Hanoi',
        zipcode: '10000',
        country: 'Vietnam'
      }
    });

    let headers = {
      'Content-Type': 'application/json',
      'X-CSRFToken': csrfToken,
    };

    let res = http.post(`${BASE_URL}/process_order/`, payload, { headers: headers });

    check(res, {
      'Order Processed (Kafka Sent)': (r) => r.status === 200 && r.body.includes('Payment complete'),
    });
  });

  sleep(1);
}
