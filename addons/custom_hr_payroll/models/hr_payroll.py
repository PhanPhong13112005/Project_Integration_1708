from odoo import models, fields, api

class HrPayslip(models.Model):
    _inherit = 'hr.payslip'
    _description = 'Tính lương dựa trên chấm công thực tế'

    total_attendance_hours = fields.Float(
        string='Tổng giờ công thực tế',
        compute='_compute_attendance_data',
        store=True,
        help="Tổng số giờ làm việc được ghi nhận từ máy chấm công"
    )
    
    total_overtime_hours = fields.Float(
        string='Tổng giờ tăng ca (OT)',
        compute='_compute_attendance_data',
        store=True,
        help="Tổng số giờ làm vượt mức quy định (được tính từ module Attendance)"
    )

    @api.depends('employee_id', 'date_from', 'date_to')
    def _compute_attendance_data(self):
        """
        Hàm này sẽ chạy mỗi khi bạn chọn Nhân viên hoặc thay đổi Ngày tháng trên phiếu lương.
        Nó sẽ quét bảng hr.attendance để cộng dồn giờ làm.
        """
        for slip in self:
            if not slip.employee_id or not slip.date_from or not slip.date_to:
                slip.total_attendance_hours = 0.0
                slip.total_overtime_hours = 0.0
                continue

            attendances = self.env['hr.attendance'].search([
                ('employee_id', '=', slip.employee_id.id),
                ('check_in', '>=', slip.date_from),
                ('check_in', '<=', slip.date_to)
            ])

            total_hours = sum(attendances.mapped('worked_hours'))
            total_ot = sum(attendances.mapped('overtime_hours'))

            slip.total_attendance_hours = total_hours
            slip.total_overtime_hours = total_ot

    def compute_sheet(self):
        """
        Ghi đè hàm 'Tính toán' (Compute Sheet) của nút bấm trên giao diện.
        Mục đích: Đảm bảo dữ liệu chấm công mới nhất được cập nhật trước khi tính tiền.
        """
        self._compute_attendance_data()
        
        return super(HrPayslip, self).compute_sheet()