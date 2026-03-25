# -*- coding: utf-8 -*-
from odoo import http, fields
from odoo.http import request
import requests
import json
from datetime import datetime, time, timedelta

class NhanSuController(http.Controller):
    
    # 1. Giao diện Camera Kiosk (Tự động nhận diện)
    @http.route('/nhan_su/face_scan_kiosk', type='http', auth='user', website=True)
    def face_scan_kiosk(self, **kw):
        return request.render('nhan_su.face_scan_template', {})

    # 2. Xử lý logic Nhận diện và Chấm công
    @http.route('/nhan_su/face_recognize', type='json', auth='user', methods=['POST'], csrf=False)
    def face_recognize(self, image_data):
        try:
            # --- BƯỚC A: CHUẨN BỊ DỮ LIỆU GỬI SANG AI SERVER ---
            # Lấy tất cả nhân viên có ảnh để so khớp
            employees = request.env['nhan_vien'].sudo().search([])
            known_faces = []
            for emp in employees:
                # Ưu tiên lấy ảnh từ trường 'anh', nếu không có thì lấy 'image_1920'
                anh_goc = emp.anh or (hasattr(emp, 'image_1920') and emp.image_1920)
                if anh_goc:
                    anh_str = anh_goc.decode('utf-8') if isinstance(anh_goc, bytes) else anh_goc
                    known_faces.append({'id': emp.id, 'image': anh_str})
            
            if not known_faces:
                return {'status': 'error', 'message': 'Hệ thống chưa có ảnh mẫu nhân viên nào!'}

            # --- BƯỚC B: GỌI AI SERVER (PORT 5000) ---
            payload = {"live_image": image_data, "known_faces": known_faces}
            # Timeout 5s để tránh treo trình duyệt nếu AI Server xử lý chậm
            response = requests.post("http://127.0.0.1:5000/recognize", json=payload, timeout=10)
            result = response.json()

            # --- BƯỚC C: XỬ LÝ KẾT QUẢ TỪ AI ---
            if result.get("status") == "success":
                emp_id = result.get("emp_id")
                
                # Gọi hàm xử lý logic Vào/Ra thông minh đã viết trong Model
                # Hàm này sẽ tự tìm bản ghi trong ngày để điền check_in hoặc check_out
                status_type = request.env['cham_cong'].sudo().xu_ly_diem_danh_phong(emp_id)
                
                if status_type == "duplicate":
                    # Trả về trạng thái để JavaScript biết và hiển thị thông báo
                    return {
                        'status': 'info', 
                        'message': '🌟 Bạn đã hoàn thành chấm công hôm nay. Hẹn gặp lại vào ngày mai!'
                    }

                # Lấy thông tin nhân viên để gửi Telegram
                emp = request.env['nhan_vien'].sudo().browse(emp_id)
                ten_nv = emp.display_name or emp.ma_dinh_danh
                
                # Tính giờ Việt Nam (UTC+7) để gửi tin nhắn
                gio_vn = datetime.now() + timedelta(hours=7)
                time_str = gio_vn.strftime('%H:%M:%S')
                
                # Thiết lập nội dung thông báo dựa trên mốc 8:00 và 17:00
                if status_type == "in":
                    prefix = "✅ CHECK-IN"
                    note = " (ĐI MUỘN ⚠️)" if gio_vn.time() > time(8, 0) else " (Đúng giờ)"
                else:
                    prefix = "🚪 CHECK-OUT"
                    note = " (VỀ SỚM ⚠️)" if gio_vn.time() < time(17, 0) else " (Hoàn thành công việc)"

                # --- BƯỚC D: GỬI TELEGRAM ---
                bot_token = '8787593911:AAHJ0l2vXpxqoEv0l2ZWvCT6zLJPa_FVPbw'
                chat_id = '-1003788848010'
                msg = f"{prefix} THÀNH CÔNG\n👤 Nhân viên: {ten_nv}\n🕒 Thời gian: {time_str}{note}"
                
                try:
                    requests.post(f"https://api.telegram.org/bot{bot_token}/sendMessage", 
                                  json={"chat_id": chat_id, "text": msg}, timeout=3)
                except Exception as e:
                    print(f"Lỗi gửi Telegram: {e}")

                return {'status': 'success', 'emp_name': f"{ten_nv} ({prefix})"}
            
            # Trả về lỗi nếu AI không nhận diện được mặt
            return result 
            
        except requests.exceptions.ConnectionError:
            return {'status': 'error', 'message': 'AI Server (Port 5000) chưa bật!'}
        except Exception as e:
            return {'status': 'error', 'message': f'Lỗi hệ thống: {str(e)}'}