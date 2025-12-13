import http from 'k6/http';
import { check, sleep, group } from 'k6';
import { randomString, randomIntBetween } from 'https://jslib.k6.io/k6-utils/1.2.0/index.js';

// --- CẤU HÌNH MỤC TIÊU ---
const BASE_URL = 'http://store-backend:8000'; 
// 1. TĂNG KÍCH THƯỚC: 50KB rác mỗi request (50 * 1024)
const PADDING_SIZE = 102400;

export const options = {
  scenarios: {
    rubik_stress_test: {
      executor: 'ramping-vus',
      startVUs: 0,
      stages: [
        { duration: '30s', target: 50 },  // Khởi động
        { duration: '1m', target: 100 },   // Tăng tốc
        //{ duration: '3m', target: 100 },  // Ép tải cực đại (100 VUs) trong 3 phút
        { duration: '30s', target: 0 },    // Hạ nhiệt
      ],
      gracefulRampDown: '10s',
    },
  },
};

// Tạo sẵn chuỗi rác 50KB (Tạo 1 lần dùng chung cho đỡ tốn CPU của K6)
const JUNK_DATA = randomString(PADDING_SIZE); 

export default function () {
  const jar = http.cookieJar();
  
  // Tạo user ngẫu nhiên
  const uniqueId = `${__VU}_${__ITER}_${Date.now()}`;
  const username = `u_${uniqueId}`;
  const email = `${username}@test.com`;
  const password = 'phanquyenbtx';

  // --- GIAI ĐOẠN 1: TẠO TÀI KHOẢN (Tốn DB - Chỉ làm 1 lần) ---
  
  let regRes = http.post(`${BASE_URL}/register/`, {
    username: username, email: email, password1: password, password2: password
  }, { headers: { 'Content-Type': 'application/x-www-form-urlencoded' } });
  
  if (!check(regRes, { 'Reg OK': (r) => r.status === 200 || r.status === 302 })) return;

  let loginRes = http.post(`${BASE_URL}/login/`, {
    username: username, password: password,
  }, { headers: { 'Content-Type': 'application/x-www-form-urlencoded' } });

  if (!check(loginRes, { 'Login OK': (r) => r.status === 200 || r.status === 302 })) return;

  // --- GIAI ĐOẠN 2: SPAM MUA HÀNG (Tốn Network - Lặp lại nhiều lần) ---
  // Mỗi User sau khi login sẽ mua liên tiếp 20 đơn hàng để đẩy Kafka lên ngưỡng giới hạn
  
  const LOOP_COUNT = 20; 

  group('3. Spam Orders Loop', function () {
    let addPayload = JSON.stringify({ productId: 1, action: 'add' });
    let checkoutPayload = JSON.stringify({
      form: { name: username, email: email, total: '5000' }, // Giá 1 sản phẩm
      shipping: {
        address: '4GB Mission Street', city: 'Ho Chi Minh', state: 'HCM', zipcode: '70000',
        extra_data: JUNK_DATA // <-- 50KB nằm ở đây
      }
    });
    
    let jsonHeaders = { headers: { 'Content-Type': 'application/json' } };

    for (let i = 0; i < LOOP_COUNT; i++) {
        // 3.1. Add to Cart (Tạo session order mới)
        let resAdd = http.post(`${BASE_URL}/update_item/`, addPayload, jsonHeaders);
        check(resAdd, { 'Add OK': (r) => r.status === 200 });

        // 3.2. Checkout (Gửi 50KB đi Kafka)
        let resCheckout = http.post(`${BASE_URL}/process_order/`, checkoutPayload, jsonHeaders);
        
        check(resCheckout, { 
            'Kafka Sent': (r) => r.status === 200 && r.body.includes('Payment complete') 
        });

        // Nghỉ cực ngắn giữa các lần spam để tránh nghẽn cục bộ
        sleep(0.01); 
    }
  });
}
