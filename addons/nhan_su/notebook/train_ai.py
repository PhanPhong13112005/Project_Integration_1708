import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
import joblib

# 1. Đọc dữ liệu
data = pd.read_csv('data_train.csv')

# 2. CHỈ CHỌN 3 CỘT SỐ LIỆU NÀY ĐỂ AI HỌC (Bỏ qua tên và tháng)
X = data[['so_gio_lam', 'so_lan_muon', 'nghi_khong_phep']]
y = data['label']

# 3. Chia tập huấn luyện
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# 4. Huấn luyện AI
model = RandomForestClassifier(n_estimators=100, random_state=42)
model.fit(X_train, y_train)

# 5. Lưu não bộ AI
joblib.dump(model, 'model_du_bao_nghi_viec.pkl')
print("✅ Huấn luyện thành công! AI đã tìm ra quy luật nghỉ việc.")