import pandas as pd
import os
import joblib
from sklearn.ensemble import RandomForestClassifier
import sys

# --- BƯỚC 1: XÁC ĐỊNH ĐƯỜNG DẪN TUYỆT ĐỐI ---
# Lấy đường dẫn của chính file train_ai.py này (.../nhan_su/notebook/)
base_dir = os.path.dirname(os.path.abspath(__file__))

# Đường dẫn file CSV (nhảy ra ngoài notebook/ để vào data/raw/)
csv_path = os.path.join(base_dir, '..', 'data', 'raw', 'data_train.csv')

# Đường dẫn lưu file Model .pkl (nhảy ra ngoài notebook/ để vào data/outputs/)
model_output_path = os.path.join(base_dir, '..', 'data', 'outputs', 'model_du_bao_nghi_viec.pkl')

print(f"--- Đang đọc dữ liệu từ: {csv_path} ---")

# Kiểm tra file CSV có tồn tại không
if not os.path.exists(csv_path):
    print(f"LỖI: Không tìm thấy file {csv_path}")
    sys.exit(1)

# --- BƯỚC 2: HUẤN LUYỆN ---
try:
    data = pd.read_csv(csv_path)
    
    # Chọn các cột đặc trưng (Features) và nhãn (Label)
    # Lưu ý: Tên cột phải khớp với file CSV bạn đã xuất từ cham_cong.py
    X = data[['so_gio_lam', 'so_lan_muon', 'nghi_khong_phep']]
    y = data['label']

    # Khởi tạo mô hình
    model = RandomForestClassifier(n_estimators=100, random_state=42)
    model.fit(X, y)

    # --- BƯỚC 3: LƯU MÔ HÌNH ---
    # Tạo thư mục outputs nếu chưa có
    os.makedirs(os.path.dirname(model_output_path), exist_ok=True)
    
    joblib.dump(model, model_output_path)
    print(f"--- HUẤN LUYỆN THÀNH CÔNG! Đã lưu tại: {model_output_path} ---")

except Exception as e:
    print(f"LỖI TRONG QUÁ TRÌNH HUẤN LUYỆN: {str(e)}")
    sys.exit(1)