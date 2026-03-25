# file: nhan_su/models/du_bao.py
from odoo import models, fields, api
import os
import joblib
import logging

_logger = logging.getLogger(__name__)

class DuBaoNghiViec(models.Model):
    _name = 'ns.du.bao'
    _description = 'Hệ thống AI Dự báo Nhân sự'

    # Thông tin nhân viên
    nhan_vien_id = fields.Many2one('nhan_vien', string='Nhân viên', required=True)
    
    # 3 thông số đầu vào cho AI
    so_gio_lam = fields.Float(string='Số giờ làm (tháng)', required=True, default=0.0)
    so_lan_muon = fields.Integer(string='Số lần đi muộn', required=True, default=0)
    nghi_khong_phep = fields.Integer(string='Số ngày nghỉ không phép', required=True, default=0)
    
    # Kết quả AI trả về
    diem_rui_ro = fields.Float(string='Tỷ lệ rủi ro (%)', compute='_compute_ai_predict', store=True)
    muc_do_canh_bao = fields.Selection([
        ('an_toan', 'An Toàn'),
        ('canh_bao', 'Cảnh Báo'),
        ('nguy_hiem', 'Nguy Hiểm')
    ], string='Mức độ', compute='_compute_ai_predict', store=True)
    phan_tich_chi_tiet = fields.Text(string='AI Phân tích', compute='_compute_ai_predict', store=True)

    # --- HÀM 1: DỰ BÁO TỰ ĐỘNG KHI CÓ DỮ LIỆU (COMPUTE) ---
    @api.depends('so_gio_lam', 'so_lan_muon', 'nghi_khong_phep')
    def _compute_ai_predict(self):
        base_dir = os.path.dirname(os.path.abspath(__file__))
        model_path = os.path.join(base_dir, '../data/outputs/model_du_bao_nghi_viec.pkl')
        
        try:
            model = joblib.load(model_path)
        except Exception as e:
            _logger.error(f"Lỗi tải Model AI: {e}")
            model = None

        for r in self:
            if not model:
                r.diem_rui_ro = 0.0
                r.muc_do_canh_bao = 'an_toan'
                r.phan_tich_chi_tiet = "⚠️ Chưa tìm thấy file Model AI (.pkl). Hãy huấn luyện mô hình trước."
                continue

            input_data = [[r.so_gio_lam, r.so_lan_muon, r.nghi_khong_phep]]
            # AI tính toán xác suất
            prob = model.predict_proba(input_data)[0][1] * 100
            
            r.diem_rui_ro = prob
            if prob < 30:
                r.muc_do_canh_bao = 'an_toan'
                r.phan_tich_chi_tiet = "✅ Nhân viên gắn bó tốt. Cần tiếp tục duy trì chính sách đãi ngộ."
            elif prob < 70:
                r.muc_do_canh_bao = 'canh_bao'
                r.phan_tich_chi_tiet = "⚠️ Có dấu hiệu lơ là công việc. Quản lý nên gặp mặt trao đổi."
            else:
                r.muc_do_canh_bao = 'nguy_hiem'
                r.phan_tich_chi_tiet = f"🚨 CẢNH BÁO: Nguy cơ nghỉ việc rất cao ({prob:.1f}%). Cần có phương án thay thế hoặc giữ chân gấp!"

    # --- HÀM 2: AI QUÉT TOÀN BỘ CÔNG TY (DÙNG CHO NÚT BẤM) ---
    @api.model
    def action_chay_du_bao_hang_loat(self):
        # Xóa dữ liệu cũ
        self.search([]).unlink()
        
        nhan_viens = self.env['nhan_vien'].search([])
        for nv in nhan_viens:
            # Lấy lịch sử từ bảng cham_cong
            ccs = self.env['cham_cong'].search([('nhan_vien_id', '=', nv.id)])
            if not ccs:
                continue
                
            tong_gio = sum(ccs.mapped('so_gio_lam'))
            so_lan_muon = len(ccs.filtered(lambda x: x.di_muon == True))
            
            self.create({
                'nhan_vien_id': nv.id,
                'so_gio_lam': tong_gio,
                'so_lan_muon': so_lan_muon,
                'nghi_khong_phep': 0,
            })

    # --- HÀM 3: TỰ ĐỘNG LẤY DỮ LIỆU CHO 1 BẢN GHI ---
    def action_tu_dong_lay_du_lieu(self):
        for r in self:
            if r.nhan_vien_id:
                ccs = self.env['cham_cong'].search([('nhan_vien_id', '=', r.nhan_vien_id.id)])
                r.so_gio_lam = sum(ccs.mapped('so_gio_lam'))
                r.so_lan_muon = len(ccs.filtered(lambda x: x.di_muon == True))
                r.nghi_khong_phep = 0