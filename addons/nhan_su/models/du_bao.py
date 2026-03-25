# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import UserError
import os
import sys
import joblib
import subprocess
import logging

_logger = logging.getLogger(__name__)

class DuBaoNghiViec(models.Model):
    _name = 'ns.du.bao'
    _description = 'Hệ thống AI Dự báo Nhân sự'
    # Sắp xếp: Ai có điểm rủi ro cao nhất sẽ hiện lên đầu danh sách và biểu đồ
    _order = 'diem_rui_ro desc'

    nhan_vien_id = fields.Many2one('nhan_vien', string='Nhân viên', required=True)
    
    # 3 thông số đầu vào cho AI
    so_gio_lam = fields.Float(string='Số giờ làm (tháng)', default=0.0)
    so_lan_muon = fields.Integer(string='Số lần đi muộn', default=0)
    nghi_khong_phep = fields.Integer(string='Số ngày nghỉ không phép', default=0)
    
    # Kết quả AI trả về (Lưu vào database để vẽ biểu đồ)
    diem_rui_ro = fields.Float(string='Tỷ lệ rủi ro (%)', compute='_compute_ai_predict', store=True)
    muc_do_canh_bao = fields.Selection([
        ('an_toan', 'An Toàn'),
        ('canh_bao', 'Cảnh Báo'),
        ('nguy_hiem', 'Nguy Hiểm')
    ], string='Mức độ', compute='_compute_ai_predict', store=True)
    phan_tich_chi_tiet = fields.Text(string='AI Phân tích', compute='_compute_ai_predict', store=True)

    @api.depends('so_gio_lam', 'so_lan_muon', 'nghi_khong_phep')
    def _compute_ai_predict(self):
        """Hàm nạp Model AI (.pkl) để tính toán xác suất"""
        # Xác định đường dẫn file model .pkl trong thư mục data/outputs
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        model_path = os.path.join(base_dir, 'data/outputs/model_du_bao_nghi_viec.pkl')
        
        try:
            model = joblib.load(model_path)
        except Exception as e:
            _logger.error(f"Không thể nạp file Model AI: {e}")
            model = None

        for r in self:
            if not model:
                r.diem_rui_ro = 0.0
                r.muc_do_canh_bao = 'an_toan'
                r.phan_tich_chi_tiet = "⚠️ Hệ thống đang chờ được huấn luyện mô hình AI..."
                continue

            # Đưa dữ liệu vào mô hình dự đoán
            input_data = [[r.so_gio_lam, r.so_lan_muon, r.nghi_khong_phep]]
            # Lấy xác suất của nhãn 1 (Nghỉ việc)
            prob = model.predict_proba(input_data)[0][1] * 100
            
            r.diem_rui_ro = prob
            if prob < 30:
                r.muc_do_canh_bao = 'an_toan'
                r.phan_tich_chi_tiet = "✅ Nhân viên có biểu hiện gắn bó tốt. Cần tiếp tục duy trì chính sách đãi ngộ hiện tại."
            elif prob < 70:
                r.muc_do_canh_bao = 'canh_bao'
                r.phan_tich_chi_tiet = "⚠️ Có dấu hiệu lơ là công việc hoặc chưa hài lòng. Quản lý trực tiếp nên gặp mặt trao đổi."
            else:
                r.muc_do_canh_bao = 'nguy_hiem'
                r.phan_tich_chi_tiet = f"🚨 CẢNH BÁO ĐỎ: Nguy cơ nghỉ việc lên tới {prob:.1f}%. Đề nghị phòng Nhân sự có phương án giữ chân hoặc thay thế gấp!"

    def action_train_and_predict(self):
            # 1. Lấy đường dẫn gốc của module 'nhan_su'
            this_file_path = os.path.dirname(os.path.abspath(__file__))
            module_root = os.path.abspath(os.path.join(this_file_path, '..')) 
            
            # 2. CHỈ ĐÚNG CHỖ: Thêm 'notebook' vào đường dẫn
            script_path = os.path.join(module_root, 'notebook', 'train_ai.py')

            if not os.path.exists(script_path):
                raise UserError(f"Vẫn không thấy file tại: {script_path}")

            try:
                # 3. Chạy huấn luyện bằng Python của môi trường ảo
                subprocess.run([sys.executable, script_path], check=True, capture_output=True)
                
                # Quét lại dữ liệu để cập nhật biểu đồ
                self.action_chay_du_bao_hang_loat()
            except subprocess.CalledProcessError as e:
                raise UserError(f"Lỗi khi chạy script AI: {e.stderr.decode()}")

            return True

    def action_chay_du_bao_hang_loat(self):
        """Quét toàn bộ nhân viên để lấy dữ liệu chấm công thực tế và đưa vào bảng dự báo"""
        # Xóa các bản ghi cũ để làm mới dữ liệu
        self.search([]).unlink()
        
        nhan_viens = self.env['nhan_vien'].search([])
        for nv in nhan_viens:
            # Lấy lịch sử chấm công từ bảng 'cham_cong'
            ccs = self.env['cham_cong'].search([('nhan_vien_id', '=', nv.id)])
            if not ccs:
                continue
                
            tong_gio = sum(ccs.mapped('so_gio_lam'))
            # Đếm số lần đi muộn (dựa trên trường boolean di_muon của bạn)
            so_lan_muon = len(ccs.filtered(lambda x: x.di_muon == True))
            
            # Tạo bản ghi mới (Odoo sẽ tự gọi _compute_ai_predict để tính điểm)
            self.create({
                'nhan_vien_id': nv.id,
                'so_gio_lam': tong_gio,
                'so_lan_muon': so_lan_muon,
                'nghi_khong_phep': 0, # Mặc định là 0
            })

    def action_tu_dong_lay_du_lieu(self):
        """Hàm thủ công dùng trong Form view để lấy số liệu cho 1 người"""
        for r in self:
            if r.nhan_vien_id:
                ccs = self.env['cham_cong'].search([('nhan_vien_id', '=', r.nhan_vien_id.id)])
                r.write({
                    'so_gio_lam': sum(ccs.mapped('so_gio_lam')),
                    'so_lan_muon': len(ccs.filtered(lambda x: x.di_muon == True)),
                    'nghi_khong_phep': 0
                })