import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
import joblib
import os

# 1. Xác định đường dẫn dựa trên vị trí file code hiện tại (đang ở trong 'notebook')
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CSV_PATH = os.path.join(BASE_DIR, '../data/raw/data_train.csv')
MODEL_PATH = os.path.join(BASE_DIR, '../data/outputs/model_du_bao_nghi_viec.pkl')

print(f"Đang đọc dữ liệu từ: {CSV_PATH}")
data = pd.read_csv(CSV_PATH)

# 2. Chọn dữ liệu huấn luyện
X = data[['so_gio_lam', 'so_lan_muon', 'nghi_khong_phep']]
y = data['label']

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

print("Đang tiến hành huấn luyện AI (Random Forest)...")
model = RandomForestClassifier(n_estimators=100, random_state=42)
model.fit(X_train, y_train)

# 3. Đánh giá độ chính xác
score = model.score(X_test, y_test)
print(f"Độ chính xác của mô hình: {score * 100}%")

# 4. Lưu bộ não AI vào thư mục data/outputs/
joblib.dump(model, MODEL_PATH)
print(f"✅ Hoàn tất! File Model đã được lưu tại:\n {MODEL_PATH}")