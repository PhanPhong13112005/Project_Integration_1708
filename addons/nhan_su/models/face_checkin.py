import cv2
import face_recognition
import xmlrpc.client
import numpy as np
import base64
from datetime import datetime
import time

# ================= 1. CẤU HÌNH KẾT NỐI ODOO =================
# BẠN HÃY SỬA 4 DÒNG NÀY CHO ĐÚNG VỚI ODOO CỦA BẠN NHÉ
URL = 'http://localhost:8069'
DB = 'business_internship'  # <-- SỬA TÊN DATABASE Ở ĐÂY
USERNAME = 'admin@gmail.com'           # <-- SỬA TÀI KHOẢN
PASSWORD = '123'               # <-- SỬA MẬT KHẨU

print("1. Đang kết nối tới Odoo...")
try:
    common = xmlrpc.client.ServerProxy('{}/xmlrpc/2/common'.format(URL))
    uid = common.authenticate(DB, USERNAME, PASSWORD, {})
    models = xmlrpc.client.ServerProxy('{}/xmlrpc/2/object'.format(URL))
    if not uid:
        print("Đăng nhập Odoo thất bại! Vui lòng kiểm tra lại DB, User, Password.")
        exit()
    print("   -> Kết nối thành công!")
except Exception as e:
    print(f"Lỗi kết nối: {e}")
    exit()

# ================= 2. TẢI DỮ LIỆU "HỌC" TỪ ODOO =================
print("2. Đang tải ảnh Avatar từ Odoo để AI trích xuất đặc trưng...")
nhan_vien_list = models.execute_kw(DB, uid, PASSWORD,
    'nhan_vien', 'search_read',
    [[['anh', '!=', False]]], 
    {'fields': ['id', 'ho_va_ten', 'anh']}
)

known_face_encodings = []
known_face_names = []
known_face_ids = []

for nv in nhan_vien_list:
    try:
        img_data = base64.b64decode(nv['anh'])
        nparr = np.frombuffer(img_data, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        encodings = face_recognition.face_encodings(img)
        if len(encodings) > 0:
            known_face_encodings.append(encodings[0])
            known_face_names.append(f"{nv['ho_va_ten']}")
            known_face_ids.append(nv['id'])
            print(f"   - Đã học xong khuôn mặt: {nv['ho_va_ten']}")
    except Exception as e:
        pass

print(f"==> Hoàn tất! Đã trích xuất {len(known_face_encodings)} khuôn mặt.")

# ================= 3. BẬT CAMERA VÀ CHẤM CÔNG =================
print("\n3. Đang bật Webcam... (Nhấn phím 'q' trên cửa sổ camera để thoát)")
video_capture = cv2.VideoCapture(0)

# Kiểm tra xem máy ảo Ubuntu có gọi được Camera của Windows không
if not video_capture.isOpened():
    print("\n[LỖI CẢNH BÁO]: Không thể mở Camera!")
    print("Nguyên nhân: Môi trường máy ảo Ubuntu (WSL) mặc định chưa được cấp quyền dùng Webcam của Windows.")
    exit()

last_checkin = {} # Bộ đệm chống spam gửi Odoo liên tục

while True:
    ret, frame = video_capture.read()
    if not ret: break

    # Thu nhỏ ảnh để AI xử lý mượt mà, không bị giật lag
    small_frame = cv2.resize(frame, (0, 0), fx=0.25, fy=0.25)
    rgb_small_frame = small_frame[:, :, ::-1]

    # Tìm khuôn mặt trong khung hình
    face_locations = face_recognition.face_locations(rgb_small_frame)
    face_encodings = face_recognition.face_encodings(rgb_small_frame, face_locations)

    for face_encoding, face_location in zip(face_encodings, face_locations):
        name = "Unknown"
        # So sánh khuôn mặt trong cam với dữ liệu đã học
        face_distances = face_recognition.face_distance(known_face_encodings, face_encoding)
        
        if len(face_distances) > 0:
            best_match_index = np.argmin(face_distances)
            
            # Sai số < 0.5 là cực kỳ giống (tránh nhận nhầm người)
            if face_distances[best_match_index] < 0.5:
                name = known_face_names[best_match_index]
                nv_id = known_face_ids[best_match_index]

                # --- GỬI LỆNH CHẤM CÔNG LÊN ODOO ---
                now = time.time()
                # 60 giây mới cho phép điểm danh 1 lần để tránh spam
                if nv_id not in last_checkin or (now - last_checkin[nv_id] > 60):
                    print(f"\n--> NHẬN DIỆN THÀNH CÔNG: {name}")
                    try:
                        check_in_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                        models.execute_kw(DB, uid, PASSWORD, 'cham_cong', 'create', [{
                            'nhan_vien_id': nv_id,
                            'check_in': check_in_time,
                            'ghi_chu': 'Hệ thống AI FaceID'
                        }])
                        print(f"    [OK] Đã lưu chấm công vào Odoo!")
                        last_checkin[nv_id] = now
                    except Exception as e:
                        print(f"    [LỖI] Không thể gửi Odoo: {e}")

        # Vẽ khung màu xanh hiển thị lên màn hình
        top, right, bottom, left = face_location
        top *= 4; right *= 4; bottom *= 4; left *= 4
        color = (0, 255, 0) if name != "Unknown" else (0, 0, 255)
        cv2.rectangle(frame, (left, top), (right, bottom), color, 2)
        cv2.putText(frame, name, (left + 6, bottom - 6), cv2.FONT_HERSHEY_DUPLEX, 0.6, (255, 255, 255), 1)

    cv2.imshow('He Thong Cham Cong AI', frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

video_capture.release()
cv2.destroyAllWindows()
