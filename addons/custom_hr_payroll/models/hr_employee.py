from odoo import models, fields, api

class HrEmployee(models.Model):
    _inherit = 'hr.employee'
    _description = 'Cải tiến thông tin nhân viên cho tính lương'

    attendance_machine_id = fields.Char(string='Mã máy chấm công', help="ID của nhân viên trên máy chấm công vân tay/khuôn mặt")
    
    social_insurance_number = fields.Char(string='Số sổ bảo hiểm xã hội')
    tax_id_number = fields.Char(string='Mã số thuế cá nhân')

    total_hours_month = fields.Float(
        string='Tổng giờ làm tháng này', 
        compute='_compute_total_hours_month',
        help="Tổng số giờ chấm công thực tế của nhân viên trong tháng hiện tại"
    )

    def _compute_total_hours_month(self):
        """Logic tính toán sơ bộ để hiển thị trên hồ sơ nhân sự"""
        for employee in self:
            attendances = self.env['hr.attendance'].search([
                ('employee_id', '=', employee.id),
            ])
            employee.total_hours_month = sum(attendances.mapped('worked_hours'))