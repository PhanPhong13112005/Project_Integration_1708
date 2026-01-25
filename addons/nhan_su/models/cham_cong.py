# file: nhan_su/models/cham_cong.py
from odoo import models, fields, api
from odoo.exceptions import ValidationError
from datetime import datetime, time

class ChamCong(models.Model):
    _name = 'cham_cong'
    _description = 'Chấm công nhân viên'
    _order = 'check_in desc'

    nhan_vien_id = fields.Many2one('nhan_vien', string='Nhân viên', required=True)
    check_in = fields.Datetime(string='Giờ vào', required=True)
    check_out = fields.Datetime(string='Giờ ra')
    ghi_chu = fields.Text("Ghi chú")

    # Các trường tính toán
    so_gio_lam = fields.Float(string='Số giờ làm', compute='_compute_gio_lam', store=True)
    cong_thuc_te = fields.Float(string='Công quy đổi', compute='_compute_cong', store=True)
    di_muon = fields.Boolean(string='Đi muộn', compute='_compute_trang_thai', store=True)
    ve_som = fields.Boolean(string='Về sớm', compute='_compute_trang_thai', store=True)

    @api.depends('check_in', 'check_out')
    def _compute_gio_lam(self):
        for r in self:
            if r.check_in and r.check_out:
                delta = r.check_out - r.check_in
                r.so_gio_lam = delta.total_seconds() / 3600
            else:
                r.so_gio_lam = 0.0

    @api.depends('so_gio_lam')
    def _compute_cong(self):
        for r in self:
            # Ví dụ: làm >= 8 tiếng tính 1 công, < 4 tiếng tính 0.5 công
            if r.so_gio_lam >= 8:
                r.cong_thuc_te = 1.0
            elif r.so_gio_lam >= 4:
                r.cong_thuc_te = 0.5
            else:
                r.cong_thuc_te = 0.0

    @api.depends('check_in', 'check_out')
    def _compute_trang_thai(self):
        # Giả sử quy định: Vào sau 8:00 là muộn, Về trước 17:00 là sớm
        for r in self:
            r.di_muon = False
            r.ve_som = False
            if r.check_in:
                # Chuyển đổi múi giờ nếu cần, ở đây lấy giờ hệ thống
                check_in_time = fields.Datetime.context_timestamp(r, r.check_in).time()
                if check_in_time > time(8, 0):
                    r.di_muon = True
            
            if r.check_out:
                check_out_time = fields.Datetime.context_timestamp(r, r.check_out).time()
                if check_out_time < time(17, 0):
                    r.ve_som = True