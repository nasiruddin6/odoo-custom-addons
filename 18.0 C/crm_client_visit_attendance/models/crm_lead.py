# -*- coding: utf-8 -*-

from odoo import api, fields, models, _


class CrmLead(models.Model):
    """Extend crm.lead to add client visit tracking."""
    _inherit = 'crm.lead'

    visit_ids = fields.One2many(
        'crm.client.visit',
        'lead_id',
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

    @api.depends('visit_ids')
    def _compute_visit_count(self):
        """Count all visits for this opportunity."""
        for lead in self:
            lead.visit_count = len(lead.visit_ids)

    @api.depends('visit_ids', 'visit_ids.actual_check_in', 'visit_ids.state')
    def _compute_last_visit_date(self):
        """Get the most recent visit date."""
        for lead in self:
            completed_visits = lead.visit_ids.filtered(
                lambda v: v.state == 'completed' and v.actual_check_in
            )
            if completed_visits:
                lead.last_visit_date = max(
                    completed_visits.mapped('actual_check_in')
                )
            else:
                lead.last_visit_date = False

    def action_view_visits(self):
        """Open client visits for this opportunity."""
        self.ensure_one()

        return {
            'name': _('Client Visits'),
            'type': 'ir.actions.act_window',
            'res_model': 'crm.client.visit',
            'view_mode': 'list,form,kanban,calendar',
            'domain': [('lead_id', '=', self.id)],
            'context': {
                'default_lead_id': self.id,
                'default_client_id': self.partner_id.id,
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
                'default_lead_id': self.id,
                'default_client_id': self.partner_id.id,
                'default_visit_type': 'sales',
            },
            'target': 'new',
        }

