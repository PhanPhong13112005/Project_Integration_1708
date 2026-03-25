# file: nhan_su/models/bang_luong.py
import requests
from odoo import models, fields, api
from odoo.exceptions import UserError
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
            
    def action_send_telegram_luong(self):
        bot_token = '8787593911:AAHJ0l2vXpxqoEv0l2ZWvCT6zLJPa_FVPbw'
        chat_id = '-1003788848010'
        
        for r in self:
            if not r.tong_thuc_linh:
                raise UserError("Bảng lương này chưa có thực lĩnh!")
                
            # Tạo nội dung tin nhắn
            message = (f"📢 THÔNG BÁO LƯƠNG T{r.thang}/{r.nam} 📢\n"
                       f"👤 Nhân viên: {r.nhan_vien_id.ho_va_ten}\n"
                       f"✅ Tổng ngày công: {r.tong_ngay_cong}\n"
                       f"⚠️ Số lần đi muộn: {r.so_lan_di_muon}\n"
                       f"💰 TỔNG THỰC LĨNH: {r.tong_thuc_linh:,.0f} VNĐ")
            
            url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
            payload = {"chat_id": chat_id, "text": message}
            
            try:
                response = requests.post(url, json=payload)
                response.raise_for_status()
            except Exception as e:
                raise UserError(f"Lỗi khi gửi Telegram: {str(e)}")
                
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Thành công',
                'message': 'Đã gửi thông báo lương qua Telegram!',
                'type': 'success',
                'sticky': False,
            }
        }