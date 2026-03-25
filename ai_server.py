# file: ~/Project_Integration_1708/ai_server.py
from flask import Flask, request, jsonify
import face_recognition
import numpy as np
import cv2
import base64

app = Flask(__name__)

@app.route('/verify', methods=['POST'])
def verify_face():
    try:
        data = request.json
        img_data = data.get('image')
        target_img_data = data.get('target_image')

        if not img_data or not target_img_data:
            return jsonify({"status": "error", "message": "Thiếu dữ liệu ảnh"})

        # Giải mã ảnh từ camera
        img_bytes = base64.b64decode(img_data.split(',')[1])
        nparr = np.frombuffer(img_bytes, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        rgb_img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

        # Giải mã ảnh hồ sơ
        target_bytes = base64.b64decode(target_img_data)
        target_nparr = np.frombuffer(target_bytes, np.uint8)
        target_img = cv2.imdecode(target_nparr, cv2.IMREAD_COLOR)
        if target_img is None:
            return jsonify({"status": "error", "message": "Ảnh hồ sơ bị hỏng"})
        target_rgb = cv2.cvtColor(target_img, cv2.COLOR_BGR2RGB)

        # Trích xuất và so sánh
        curr_enc = face_recognition.face_encodings(rgb_img)
        target_enc = face_recognition.face_encodings(target_rgb)

        if curr_enc and target_enc:
            match = face_recognition.compare_faces([target_enc[0]], curr_enc[0], tolerance=0.6)
            if match[0]:
                return jsonify({"status": "success"})
            
        return jsonify({"status": "fail"})

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})
# Mở file ai_server.py và thêm đoạn này xuống dưới cùng (trước dòng if __name__ == '__main__':)

@app.route('/recognize', methods=['POST'])
def recognize_face():
    try:
        data = request.json
        live_image_data = data.get('live_image')
        known_faces = data.get('known_faces', []) # Nhận danh sách tất cả nhân viên

        if not live_image_data or not known_faces:
            return jsonify({"status": "error", "message": "Thiếu dữ liệu để nhận diện"})

        # Giải mã ảnh từ camera
        img_bytes = base64.b64decode(live_image_data.split(',')[1])
        nparr = np.frombuffer(img_bytes, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        rgb_live_img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

        # Lấy khuôn mặt từ Camera
        live_encodings = face_recognition.face_encodings(rgb_live_img)
        if not live_encodings:
            return jsonify({"status": "error", "message": "Không tìm thấy khuôn mặt nào..."})
        live_enc = live_encodings[0]

        # Đem khuôn mặt đó đi so sánh với TẤT CẢ nhân viên trong Database
        for person in known_faces:
            target_bytes = base64.b64decode(person['image'])
            target_nparr = np.frombuffer(target_bytes, np.uint8)
            target_img = cv2.imdecode(target_nparr, cv2.IMREAD_COLOR)
            if target_img is None: continue
            
            target_rgb = cv2.cvtColor(target_img, cv2.COLOR_BGR2RGB)
            target_encodings = face_recognition.face_encodings(target_rgb)
            
            if target_encodings:
                target_enc = target_encodings[0]
                match = face_recognition.compare_faces([target_enc], live_enc, tolerance=0.55)
                if match[0]:
                    # Nếu thấy giống ai đó, trả về luôn ID của người đó
                    return jsonify({"status": "success", "emp_id": person['id']})

        return jsonify({"status": "fail", "message": "Khuôn mặt lạ! Không có trong hệ thống."})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})

if __name__ == '__main__':
    app.run(port=5000)