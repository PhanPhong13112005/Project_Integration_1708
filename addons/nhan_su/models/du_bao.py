from odoo import models, fields, api
import os
import joblib
import logging

_logger = logging.getLogger(__name__)

class DuBaoNghiViec(models.Model):
    _name = 'ns.du.bao'
    _description = 'Hệ thống AI Dự báo Nhân sự'

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

    # --- HÀM 1: DỰ BÁO TỰ ĐỘNG KHI NHẬP TAY (FORM VIEW) ---
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
            prob = model.predict_proba(input_data)[0][1] * 100
            
            r.diem_rui_ro = prob
            if prob < 30:
                r.muc_do_canh_bao = 'an_toan'
                r.phan_tich_chi_tiet = "✅ Nhân viên có biểu hiện tốt, gắn bó với công ty. Cần tiếp tục phát huy."
            elif prob < 70:
                r.muc_do_canh_bao = 'canh_bao'
                r.phan_tich_chi_tiet = "⚠️ Dấu hiệu chán việc nhẹ. Cần quản lý hỏi thăm, động viên."
            else:
                r.muc_do_canh_bao = 'nguy_hiem'
                r.phan_tich_chi_tiet = f"🚨 CẢNH BÁO ĐỎ: Nguy cơ nghỉ việc lên tới {prob:.1f}%. Đề nghị HR can thiệp ngay!"

    # --- HÀM 2: AI QUÉT TOÀN BỘ CÔNG TY (TREE VIEW / NÚT ĐỎ) ---
    @api.model
    def action_chay_du_bao_hang_loat(self):
        # 1. Xóa hết dữ liệu cũ trên bảng để làm mới
        self.search([]).unlink()
        
        # 2. Lấy danh sách toàn bộ nhân viên
        nhan_viens = self.env['nhan_vien'].search([])
        
        for nv in nhan_viens:
            # Tìm lịch sử chấm công của nhân viên này
            ccs = self.env['cham_cong'].search([('nhan_vien_id', '=', nv.id)])
            if not ccs:
                continue # Nếu người này chưa từng chấm công thì bỏ qua
                
            tong_gio = sum(ccs.mapped('so_gio_lam'))
            so_lan_muon = len(ccs.filtered(lambda x: x.di_muon == True))
            
            # Tạo bản ghi dự báo mới, Odoo sẽ tự động gọi hàm _compute_ai_predict ở trên
            self.create({
                'nhan_vien_id': nv.id,
                'so_gio_lam': tong_gio,
                'so_lan_muon': so_lan_muon,
                'nghi_khong_phep': 0, # Tạm mặc định là 0
            })
    # BỔ SUNG HÀM NÀY VÀO CLASS DuBaoNghiViec
    def action_tu_dong_lay_du_lieu(self):
        for r in self:
            if r.nhan_vien_id:
                # Tìm tất cả lịch sử chấm công của nhân viên này
                cac_buoi_lam = self.env['cham_cong'].search([
                    ('nhan_vien_id', '=', r.nhan_vien_id.id)
                ])
                
                # Tính tổng
                tong_gio = sum(cac_buoi_lam.mapped('so_gio_lam'))
                so_lan_muon = len(cac_buoi_lam.filtered(lambda x: x.di_muon == True))
                
                # Điền vào form, _compute_ai_predict sẽ tự động chạy theo
                r.so_gio_lam = tong_gio
                r.so_lan_muon = so_lan_muon
                r.nghi_khong_phep = 0