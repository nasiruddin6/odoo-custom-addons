from odoo import api, models, fields, _


class PropertyVisitRescheduleWizard(models.TransientModel):
    _name = 'property.visit.reschedule.wizard'
    _description = 'Property Visit Reschedule Wizard'

    visit_id = fields.Many2one('crm.property.visit', 'Visit', required=True)
    lead_id = fields.Many2one('crm.lead', 'Lead', required=True)
    date = fields.Date(string='Date of Visit', required=True)
    start = fields.Datetime(string='Start Time', required=True)
    end = fields.Datetime(string='Start Time', required=True)

    def action_re_schedule(self):
        vals = {
            'visit_date': self.date,
            'visit_start_time': self.start,
            'visit_end_time': self.end,
            'state': 're_scheduled'
        }
        self.visit_id.write(vals)
        self._action_send_message()

    def _action_send_message(self):
        body = (
            f"Property Visit\n"
            f'<span class="o-mail-Message-trackingNew me-1 fw-bold text-info">{self.visit_id.name}</span> has been <span class="text-warning me-1 fw-bold">Re-Scheduled</span> on <span class="o-mail-Message-trackingNew me-1 fw-bold text-info">{self.date}</span>'
        )
        self.lead_id.message_post(
            body=body,
            message_type='notification',
            subtype_xmlid='mail.mt_comment',
            body_is_html=True
        )


