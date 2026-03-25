# file: nhan_su/models/cham_cong.py
import requests
from odoo import models, fields, api
from odoo.exceptions import UserError, ValidationError
from datetime import datetime, time, timedelta


class ChamCong(models.Model):
    _name = 'cham_cong'
    _description = 'Chấm công nhân viên'
    _order = 'check_in desc'
    
    phut_di_muon = fields.Integer(string='Phút đi muộn', compute='_compute_trang_thai', store=True)
    ve_som = fields.Boolean(string='Về sớm', compute='_compute_trang_thai', store=True)
    nhan_vien_id = fields.Many2one('nhan_vien', string='Nhân viên', required=True , readonly=True)
    check_in = fields.Datetime(string='Giờ vào', required=True, readonly=True)
    check_out = fields.Datetime(string='Giờ ra', readonly=True)
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



    di_muon_text = fields.Selection([
        ('yes', 'Có'),
        ('no', 'Không')
    ], string='Đi muộn', compute='_compute_trang_thai', store=True)

    @api.depends('check_in', 'check_out')
    def _compute_trang_thai(self):
        for r in self:
            r.di_muon = False
            r.di_muon_text = 'no' # Mặc định là Không
            r.phut_di_muon = 0
            
            if r.check_in:
                local_check_in = fields.Datetime.context_timestamp(r, r.check_in)
                if local_check_in.time() > time(8, 0):
                    r.di_muon = True
                    r.di_muon_text = 'yes' # Hiện chữ Có
                    # Tính phút muộn
                    diff = datetime.combine(datetime.today(), local_check_in.time()) - \
                           datetime.combine(datetime.today(), time(8, 0))
                    r.phut_di_muon = int(diff.total_seconds() / 60)

                    
    def action_face_recognition(self):
        # Tìm nhân viên tương ứng với tài khoản đang đăng nhập
        # Tìm dựa trên Email hoặc Mã định danh trùng với tên đăng nhập
        user_login = self.env.user.login
        employee = self.env['nhan_vien'].sudo().search([
            '|', ('email', '=', user_login), ('ma_dinh_danh', '=', user_login)
        ], limit=1)
        
        # Nếu máy test chưa thiết lập user, ta lấy đại nhân viên đầu tiên để demo
        if not employee:
            employee = self.env['nhan_vien'].sudo().search([], limit=1)

        if not employee:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {'title': 'Lỗi', 'message': 'Không tìm thấy hồ sơ nhân viên!', 'type': 'danger'}
            }

        return {
            'type': 'ir.actions.act_url',
            'url': '/nhan_su/face_scan/%s' % employee.id,
            'target': 'new',
        }
    def action_send_telegram_nhac_nho(self):
        bot_token = '8787593911:AAHJ0l2vXpxqoEv0l2ZWvCT6zLJPa_FVPbw'
        chat_id = '-1003788848010'
        
        for r in self:
            if not r.di_muon:
                raise UserError("Nhân viên này không đi muộn, không cần nhắc nhở!")
                
            # Lấy giờ check-in theo múi giờ local (Việt Nam)
            check_in_local = fields.Datetime.context_timestamp(r, r.check_in).strftime('%d/%m/%Y %H:%M:%S')

            message = (f"⚠️ NHẮC NHỞ ĐI MUỘN ⚠️\n"
                       f"👤 Nhân viên: {r.nhan_vien_id.ho_va_ten}\n"
                       f"🕒 Giờ check-in: {check_in_local}\n"
                       f"Đề nghị nhân sự chú ý đảm bảo giờ giấc làm việc!")
            
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
                'message': 'Đã gửi nhắc nhở đi muộn qua Telegram!',
                'type': 'warning',
            }
        }
    @api.model
    def xu_ly_diem_danh_phong(self, nhan_vien_id):
        now = fields.Datetime.now()
        
        # 1. Xác định mốc thời gian bắt đầu ngày hôm nay (giờ VN)
        user_tz = self.env.user.tz or 'Asia/Ho_Chi_Minh'
        local_context = self.with_context(tz=user_tz)
        today_local = fields.Datetime.context_timestamp(local_context, now).date()
        start_of_day_utc = datetime.combine(today_local, time.min) - timedelta(hours=7)

        # 2. Tìm bản ghi chấm công của nhân viên này trong ngày hôm nay
        attendance = self.search([
            ('nhan_vien_id', '=', nhan_vien_id),
            ('check_in', '>=', start_of_day_utc)
        ], limit=1, order='check_in asc')

        if attendance:
            # Nếu ĐÃ CÓ check_out rồi thì KHÔNG làm gì nữa (tránh quét liên tục)
            if attendance.check_out:
                return "duplicate" # Hoặc trả về "done" để báo đã hoàn thành ngày công
            
            # Nếu CHƯA CÓ check_out: Kiểm tra khoảng cách 30 giây để xác nhận RA
            diff = (now - attendance.check_in).total_seconds()
            if diff > 30: 
                attendance.write({'check_out': now})
                return "out"
            return "duplicate"
        else:
            # Nếu CHƯA CÓ bản ghi nào: Tạo mới Check-in
            self.create({
                'nhan_vien_id': nhan_vien_id,
                'check_in': now,
                'ghi_chu': f"✅ Check-in: {fields.Datetime.context_timestamp(self, now).strftime('%H:%M')}"
            })
            return "in"