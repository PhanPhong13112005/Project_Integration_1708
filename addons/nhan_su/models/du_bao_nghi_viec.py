# File: nhan_su/models/du_bao_nghi_viec.py
from odoo import models, fields, api
from datetime import date, timedelta

class DuBaoNghiViec(models.Model):
    _name = 'ns.du.bao'
    _description = 'Dự báo nguy cơ nghỉ việc (Predictive Analytics)'
    _rec_name = 'nhan_vien_id'

    nhan_vien_id = fields.Many2one('nhan_vien', string='Nhân viên', required=True)
    
    # Các tham số đầu vào (Features)
    luong_hien_tai = fields.Float(related='nhan_vien_id.luong_co_ban', string='Mức lương')
    so_lan_di_muon_thang_nay = fields.Integer(string='Số lần đi muộn (30 ngày qua)', compute='_compute_chi_so')
    tham_nien_thang = fields.Integer(string='Thâm niên (Tháng)', compute='_compute_chi_so')
    
    # Kết quả dự báo (Prediction Output)
    diem_rui_ro = fields.Float(string='Tỷ lệ rủi ro (%)', compute='_compute_risk_score', store=True)
    muc_do_canh_bao = fields.Selection([
        ('thap', 'An toàn'),
        ('trung_binh', 'Cần quan tâm'),
        ('cao', 'Nguy cơ nghỉ việc cao')
    ], string='Mức độ cảnh báo', compute='_compute_risk_score', store=True)
    
    phan_tich_chi_tiet = fields.Text(string='AI Phân tích nguyên nhân', compute='_compute_risk_score')

    @api.depends('nhan_vien_id')
    def _compute_chi_so(self):
        for r in self:
            if not r.nhan_vien_id:
                r.so_lan_di_muon_thang_nay = 0
                r.tham_nien_thang = 0
                continue
            
            # 1. Tính số lần đi muộn trong 30 ngày gần nhất1`   `
            thang_nay = date.today().replace(day=1)
            so_lan_muon = self.env['cham_cong'].search_count([
                ('nhan_vien_id', '=', r.nhan_vien_id.id),
                ('check_in', '>=', thang_nay),
                ('di_muon', '=', True)
            ])
            r.so_lan_di_muon_thang_nay = so_lan_muon

            # 2. Tính thâm niên (Giả sử dựa trên ngày tạo hoặc hợp đồng - ở đây demo lấy ngày tạo)
            create_date = r.nhan_vien_id.create_date.date()
            delta = date.today() - create_date
            r.tham_nien_thang = int(delta.days / 30)

    @api.depends('luong_hien_tai', 'so_lan_di_muon_thang_nay', 'tham_nien_thang')
    def _compute_risk_score(self):
        """ Thuật toán Heuristic Scoring """
        for r in self:
            score = 0
            reasons = []

            # === TIÊU CHÍ 1: LƯƠNG (Trọng số 40%) ===
            # Giả sử mức lương trung bình thị trường là 8 triệu
            if r.luong_hien_tai < 6000000:
                score += 40
                reasons.append("- Lương thấp hơn mức trung bình thị trường.")
            elif r.luong_hien_tai < 8000000:
                score += 20
            
            # === TIÊU CHÍ 2: THÁI ĐỘ/ĐI MUỘN (Trọng số 30%) ===
            if r.so_lan_di_muon_thang_nay > 5:
                score += 30
                reasons.append(f"- Đi muộn quá nhiều ({r.so_lan_di_muon_thang_nay} lần/tháng) -> Dấu hiệu chán nản.")
            elif r.so_lan_di_muon_thang_nay > 3:
                score += 15

            # === TIÊU CHÍ 3: THÂM NIÊN (Trọng số 20%) ===
            # Người làm > 24 tháng (2 năm) thường có xu hướng nhảy việc nếu không thăng tiến
            if r.tham_nien_thang > 24 and r.luong_hien_tai < 10000000:
                score += 20
                reasons.append("- Thâm niên cao nhưng mức lương chưa tương xứng.")

            # Chốt điểm
            r.diem_rui_ro = min(score, 100) # Tối đa 100%
            r.phan_tich_chi_tiet = "\n".join(reasons) if reasons else "Nhân sự đang ổn định."

            # Gán nhãn
            if r.diem_rui_ro >= 60:
                r.muc_do_canh_bao = 'cao'
            elif r.diem_rui_ro >= 30:
                r.muc_do_canh_bao = 'trung_binh'
            else:
                r.muc_do_canh_bao = 'thap'
                # ... (Giữ nguyên các code cũ) ...

    # === THÊM HÀM NÀY VÀO CUỐI CLASS ===
    def action_analyze_risk(self):
        """ Hàm này dùng để gọi từ nút bấm trên giao diện """
        for r in self:
            # Gọi lại hàm tính toán logic
            r._compute_risk_score()
        return True 