from odoo import models, fields, api

class HrAttendance(models.Model):
    _inherit = 'hr.attendance'
    _description = 'Cải tiến Chấm công phục vụ tính lương'

    is_paid = fields.Boolean(
        string="Đã tính lương", 
        default=False, 
        readonly=True, 
        help="Đánh dấu dòng chấm công này đã được xử lý trong một phiếu lương"
    )
    
    overtime_hours = fields.Float(
        string="Giờ tăng ca (OT)", 
        compute='_compute_overtime_hours', 
        store=True
    )

    @api.depends('worked_hours')
    def _compute_overtime_hours(self):
        for record in self:
            if record.worked_hours > 8.0:
                record.overtime_hours = record.worked_hours - 8.0
            else:
                record.overtime_hours = 0.0