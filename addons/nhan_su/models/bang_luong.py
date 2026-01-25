# file: nhan_su/models/bang_luong.py
from odoo import models, fields, api
from datetime import date
import calendar

class BangLuong(models.Model):
    _name = 'bang_luong'
    _description = 'Bảng tính lương tháng'

    name = fields.Char("Mã phiếu", compute='_compute_name')
    nhan_vien_id = fields.Many2one('nhan_vien', string="Nhân viên", required=True)
    thang = fields.Integer("Tháng", default=lambda self: fields.Date.today().month)
    nam = fields.Integer("Năm", default=lambda self: fields.Date.today().year)

    # Tổng hợp từ chấm công
    tong_ngay_cong = fields.Float("Tổng ngày công", compute='_tinh_luong', store=True)
    so_lan_di_muon = fields.Integer("Số lần đi muộn", compute='_tinh_luong', store=True)

    # Tính tiền
    luong_co_ban = fields.Float("Lương cơ bản", related='nhan_vien_id.luong_co_ban') # Cần thêm trường này bên nhan_vien
    tong_thuc_linh = fields.Float("Thực lĩnh", compute='_tinh_luong', store=True)

    @api.depends('nhan_vien_id', 'thang', 'nam')
    def _compute_name(self):
        for r in self:
            r.name = f"Lương T{r.thang}/{r.nam} - {r.nhan_vien_id.ma_dinh_danh or 'NV'}"

    @api.depends('nhan_vien_id', 'thang', 'nam')
    def _tinh_luong(self):
        for r in self:
            if not r.nhan_vien_id: 
                continue
            
            # 1. Tìm tất cả phiếu chấm công trong tháng
            start_date = date(r.nam, r.thang, 1)
            last_day = calendar.monthrange(r.nam, r.thang)[1]
            end_date = date(r.nam, r.thang, last_day)

            cham_cong_recs = self.env['cham_cong'].search([
                ('nhan_vien_id', '=', r.nhan_vien_id.id),
                ('check_in', '>=', start_date),
                ('check_in', '<=', end_date)
            ])

            # 2. Cộng tổng
            r.tong_ngay_cong = sum(cham_cong_recs.mapped('cong_thuc_te'))
            r.so_lan_di_muon = sum(1 for cc in cham_cong_recs if cc.di_muon)

            # 3. Tính tiền (Ví dụ: Lương CB / 26 * Công thực tế - Phạt 50k/lần muộn)
            luong_1_ngay = (r.luong_co_ban or 5000000) / 26
            tien_phat = r.so_lan_di_muon * 50000
            r.tong_thuc_linh = (luong_1_ngay * r.tong_ngay_cong) - tien_phat