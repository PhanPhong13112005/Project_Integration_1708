# 🚀 Hệ thống Quản lý Nhân sự Tích hợp AI (Project 1708)

Dự án thực tập tốt nghiệp: Tích hợp **Odoo 15** với công nghệ **FaceID** và **Học máy (Machine Learning)** để quản lý chấm công và dự báo nhân sự.

---

## 📌 Các Tính năng Chính
* **Chấm công FaceID:** Tự động nhận diện khuôn mặt qua Camera và đồng bộ dữ liệu vào Odoo theo thời gian thực.
* **Huấn luyện AI Tự động:** Gộp quy trình xuất dữ liệu, huấn luyện mô hình Random Forest và dự báo kết quả chỉ với 1 click.
* **Phân tích Rủi ro:** Dự báo tỷ lệ nghỉ việc của nhân viên và hiển thị trực quan qua biểu đồ (Graph View).

---

## 📂 Cấu trúc Dự án
```text
Project_Integration_1708/
├── venv/                   # Môi trường ảo Python
├── odoo/                   # Mã nguồn Odoo 15 Core
├── addons/
│   └── nhan_su/            # Module Custom Quản lý nhân sự
│       ├── models/         # Logic xử lý (du_bao.py, cham_cong.py)
│       ├── views/          # Giao diện (du_bao_view.xml, cham_cong_luong_view.xml)
│       └── notebook/
│           └── train_ai.py # Script huấn luyện AI (Random Forest)
├── data/
│   ├── raw/                # Chứa file data_train.csv
│   └── outputs/            # Chứa file model_du_bao_nghi_viec.pkl
├── ai_server.py            # Flask API xử lý nhận diện khuôn mặt
├── run_ai.sh               # Script khởi chạy nhanh Server AI
└── odoo.conf               # File cấu hình Server Odoo
```
🛠 Hướng dẫn Cài đặt
1. Chuẩn bị Môi trường
Mở Terminal và kích hoạt môi trường ảo:

```bash
source venv/bin/activate
pip install flask flask-cors opencv-python face_recognition pandas scikit-learn joblib
```
2. Cấu hình Cơ sở dữ liệu
Database: business_internship

Port: 5431 (Hoặc theo cấu hình trong odoo.conf)

🏃 Hướng dẫn Khởi chạy
Bước 1: Chạy Server AI (FaceID)
Sử dụng script để tự động kích hoạt venv và chạy server:
```bash
chmod +x run_ai.sh
./run_ai.sh
```
Mặc định chạy tại: http://127.0.0.1:5000

Bước 2: Chạy Server Odoo
Mở Terminal mới và nâng cấp module để nhận các thay đổi mới nhất:
```bash
python3 odoo-bin.py -c odoo.conf -u nhan_su
```

📊 Kịch bản Demo Đồ án
Ghi nhận Dữ liệu: Thực hiện chấm công qua FaceID để bảng Chấm công có dữ liệu thực tế.

Chuẩn bị AI: Tại danh sách Chấm công, nhấn nút 💾 Lưu Dữ liệu Huấn luyện AI (CSV).

Thực thi AI: Sang menu Dự báo Nghỉ việc, nhấn nút 🔄 Huấn luyện & Dự báo AI.

Hệ thống sẽ chạy ngầm train_ai.py để tạo ra "bộ não" .pkl mới nhất.

Trình diễn: Mở chế độ Graph View (Biểu đồ) để xem danh sách nhân viên được sắp xếp theo tỷ lệ rủi ro từ cao đến thấp.

⚠️ Lưu ý Quan trọng
[!IMPORTANT]

Dữ liệu huấn luyện: Cần ít nhất 1 người có so_lan_muon >= 5 và 1 người đi muộn ít để AI không bị lỗi IndexError.

Đường dẫn file: Luôn sử dụng đường dẫn tuyệt đối trong code Python để tránh lỗi FileNotFoundError khi chạy trên các môi trường khác nhau.

Thực hiện bởi: Phan Phong