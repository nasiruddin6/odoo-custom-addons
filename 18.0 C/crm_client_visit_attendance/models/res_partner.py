# -*- coding: utf-8 -*-

from odoo import api, fields, models, _


class ResPartner(models.Model):
    """Extend res.partner to add client visit tracking."""
    _inherit = 'res.partner'

    visit_ids = fields.One2many(
        'crm.client.visit',
        'client_id',
        string='Client Visits',
    )

    visit_count = fields.Integer(
        string='Visit Count',
        compute='_compute_visit_count',
    )

    last_visit_date = fields.Datetime(
        string='Last Visit Date',
        compute='_compute_last_visit_date',
        store=True,
    )

    total_visits = fields.Integer(
        string='Total Visits',
        compute='_compute_visit_statistics',
    )

    completed_visits = fields.Integer(
        string='Completed Visits',
        compute='_compute_visit_statistics',
    )

    @api.depends('visit_ids')
    def _compute_visit_count(self):
        """Count all visits for this partner."""
        for partner in self:
            partner.visit_count = len(partner.visit_ids)

    @api.depends('visit_ids', 'visit_ids.actual_check_in', 'visit_ids.state')
    def _compute_last_visit_date(self):
        """Get the most recent visit date."""
        for partner in self:
            completed_visits = partner.visit_ids.filtered(
                lambda v: v.state == 'completed' and v.actual_check_in
            )
            if completed_visits:
                partner.last_visit_date = max(
                    completed_visits.mapped('actual_check_in')
                )
            else:
                partner.last_visit_date = False

    @api.depends('visit_ids', 'visit_ids.state')
    def _compute_visit_statistics(self):
        """Calculate visit statistics."""
        for partner in self:
            partner.total_visits = len(partner.visit_ids)
            partner.completed_visits = len(
                partner.visit_ids.filtered(lambda v: v.state == 'completed')
            )

    def action_view_visits(self):
        """Open client visits for this partner."""
        self.ensure_one()

        return {
            'name': _('Client Visits'),
            'type': 'ir.actions.act_window',
            'res_model': 'crm.client.visit',
            'view_mode': 'list,form,kanban,calendar',
            'domain': [('client_id', '=', self.id)],
            'context': {
                'default_client_id': self.id,
                'search_default_group_by_state': 1,
            },
        }

    def action_schedule_visit(self):
        """Quick action to schedule a new visit."""
        self.ensure_one()

        return {
            'name': _('Schedule Visit'),
            'type': 'ir.actions.act_window',
            'res_model': 'crm.client.visit',
            'view_mode': 'form',
            'context': {
                'default_client_id': self.id,
                'default_visit_type': 'sales',
            },
            'target': 'new',
        }


