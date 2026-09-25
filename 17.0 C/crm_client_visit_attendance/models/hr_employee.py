# -*- coding: utf-8 -*-

from odoo import api, fields, models, _


class HrEmployee(models.Model):
    """Extend hr.employee to add client visit tracking."""
    _inherit = 'hr.employee'

    visit_ids = fields.One2many(
        'crm.client.visit',
        'leader_employee_id',
        string='Client Visits',
    )

    visit_count = fields.Integer(
        string='Visit Count',
        compute='_compute_visit_count',
    )

    visit_attendance_ids = fields.One2many(
        'crm.client.visit.attendance',
        'employee_id',
        string='Visit Attendance',
    )

    visit_attendance_count = fields.Integer(
        string='Visit Attendance Count',
        compute='_compute_visit_attendance_count',
    )

    completed_visits_count = fields.Integer(
        string='Completed Visits',
        compute='_compute_visit_statistics',
    )

    pending_visits_count = fields.Integer(
        string='Pending Visits',
        compute='_compute_visit_statistics',
    )

    @api.depends('visit_ids')
    def _compute_visit_count(self):
        """Count all visits for this employee."""
        for employee in self:
            employee.visit_count = len(employee.visit_ids)

    @api.depends('visit_attendance_ids')
    def _compute_visit_attendance_count(self):
        """Count all visit attendance records for this employee."""
        for employee in self:
            employee.visit_attendance_count = len(employee.visit_attendance_ids)

    @api.depends('visit_ids', 'visit_ids.state')
    def _compute_visit_statistics(self):
        """Calculate visit statistics."""
        for employee in self:
            employee.completed_visits_count = len(
                employee.visit_ids.filtered(lambda v: v.state == 'completed')
            )
            employee.pending_visits_count = len(
                employee.visit_ids.filtered(lambda v: v.state == 'planned')
            )

    def action_view_visits(self):
        """Open client visits for this employee."""
        self.ensure_one()

        return {
            'name': _('My Client Visits'),
            'type': 'ir.actions.act_window',
            'res_model': 'crm.client.visit',
            'view_mode': 'tree,form,kanban,calendar',
            'domain': [('leader_employee_id', '=', self.id)],
            'context': {
                'default_leader_employee_id': self.id,
                'search_default_group_by_state': 1,
            },
        }

    def action_view_visit_attendance(self):
        """Open visit attendance records for this employee."""
        self.ensure_one()

        return {
            'name': _('Visit Attendance'),
            'type': 'ir.actions.act_window',
            'res_model': 'crm.client.visit.attendance',
            'view_mode': 'tree,form',
            'domain': [('employee_id', '=', self.id)],
            'context': {
                'default_employee_id': self.id,
            },
        }

