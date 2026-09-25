from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError
import logging
_logger = logging.getLogger(__name__)

AVAILABLE_PRIORITIES = [
    ('0', 'Low'),
    ('1', 'Medium'),
    ('2', 'High'),
    ('3', 'Very High'),
]

class CrmPropertyVisit(models.Model):
    _name = 'crm.property.visit'
    _description = 'CRM Property Visit Schedule'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'visit_date desc, id desc'
    _rec_name = 'name'

    # ------------------------------------------------------------
    # 1. Core Visit Information (Mandatory)
    # ------------------------------------------------------------

    name = fields.Char(
        string="Visit Reference",
        required=True,
        copy=False,
        readonly=True,
        default=lambda self: 'New'
    )
    lead_id = fields.Many2one(
        'crm.lead',
        string="Lead / Opportunity",
        required=True,
        ondelete='cascade'
    )

    visit_date = fields.Date(
        string="Visit Date",
        required=True
    )

    visit_start_time = fields.Datetime(
        string="Visit Start Time",
        required=True
    )

    visit_end_time = fields.Datetime(
        string="Visit End Time",
        required=True
    )

    duration = fields.Float(
        string="Duration",
        compute='_compute_duration',
        store=True,
        readonly=True
    )

    state = fields.Selection(
        [
            ('draft', 'Draft'),
            ('planned', 'Planned'),
            ('in_progress', 'In Progress'),
            ('review', 'Under Review'),
            ('completed', 'Completed'),
            ('missed', 'Missed'),
            ('cancelled', 'Cancelled'),
            ('re_scheduled', 'Re-Scheduled'),
        ],
        string='Status',
        default='draft',
        required=True,
        tracking=True,
        index=True,
    )

    visit_purpose = fields.Selection([
        ('site', 'Site Visit'),
        ('negotiation', 'Negotiation'),
        ('followup', 'Follow-up'),
    ], string="Visit Purpose", required=True)

    priority = fields.Selection(AVAILABLE_PRIORITIES, string="Priority", default='0')

    is_need_manager_approval = fields.Boolean('Manager Approval')

    # ------------------------------------------------------------
    # 2. Property Details
    # ------------------------------------------------------------
    property_id = fields.Many2one('property.property', string="Property", related="lead_id.property_id")
    unit_id = fields.Many2one('property.unit', string="Unit", related="lead_id.unit_id")

    # ------------------------------------------------------------
    # 3. Employee & Team Assignment
    # ------------------------------------------------------------
    user_id = fields.Many2one('res.users', string="Agent/User")
    user_ids = fields.Many2many('res.users', string="Additional Agents/ Additional Users")
    team_id = fields.Many2one('crm.team', string="Sales Team")

    # ------------------------------------------------------------
    # 4. Client / Contact Information
    # ------------------------------------------------------------
    partner_id = fields.Many2one('res.partner', string="Client",)
    phone = fields.Char("Mobile", related="partner_id.phone")
    email = fields.Char("email", related="partner_id.email")
    attendees_number = fields.Integer('Number of Attendees', default=1)
    special_request = fields.Text("Special Request")

    # ------------------------------------------------------------
    # 5. Location & Logistics
    # ------------------------------------------------------------
    meeting_point = fields.Char("Exact Meeting Point")
    map_link = fields.Char("Google Map Link")
    expected_travel_time = fields.Float("Expected Travel Time")
    transport_mode = fields.Selection([
        ('bike', 'Bike'),
        ('car', 'Car'),
        ('public_transport', 'Public Transport'),
    ])
    is_parking_required = fields.Boolean('Parking Required')
    note = fields.Html(string="Internal Note")
    client_remarks = fields.Html(string="Client Remarks")

    # ------------------------------------------------------------
    # Attachments
    # ------------------------------------------------------------
    photo_ids = fields.Many2many(
        'ir.attachment',
        'visit_photo_rel',
        'visit_id',
        'attachment_id',
        string='Photos',
        help='Upload photos from the visit',
    )

    document_ids = fields.Many2many(
        'ir.attachment',
        'visit_document_rel',
        'visit_id',
        'attachment_id',
        string='Documents',
        help='Upload documents related to the visit',
    )

    signed_form_ids = fields.Many2many(
        'ir.attachment',
        'visit_signed_form_rel',
        'visit_id',
        'attachment_id',
        string='Signed Forms',
        help='Upload signed forms or agreements from the visit',
    )

    visiting_card_ids = fields.Many2many(
        'ir.attachment',
        'visit_visiting_card_rel',
        'visit_id',
        'attachment_id',
        string='Visiting Cards',
        help='Upload photos of visiting cards received during the visit',
    )

    photo_count = fields.Integer(
        string='Photos Count',
        compute='_compute_attachment_counts',
    )

    document_count = fields.Integer(
        string='Documents Count',
        compute='_compute_attachment_counts',
    )

    signed_form_count = fields.Integer(
        string='Signed Forms Count',
        compute='_compute_attachment_counts',
    )

    visiting_card_count = fields.Integer(
        string='Visiting Cards Count',
        compute='_compute_attachment_counts',
    )

    total_attachment_count = fields.Integer(
        string='Total Attachments',
        compute='_compute_attachment_counts',
    )

    # ------------------------------------------------------------
    # Attachments
    # ------------------------------------------------------------
    outcome = fields.Selection(
        [
            ('successful', 'Successful'),
            ('follow_up_required', 'Follow-up Required'),
            ('rescheduled', 'Rescheduled'),
            ('no_show', 'Client No-Show'),
        ],
        string='Outcome',
        tracking=True,
    )

    interest_level = fields.Integer(
        string='Interest Level (%)',
        tracking=True,
        help='Client interest level in percentage (0-100)',
    )

    expected_value = fields.Monetary(
        string='Expected Value',
        currency_field='currency_id',
        tracking=True,
        help='Expected sales value from this visit (for sales-related visits)',
    )

    currency_id = fields.Many2one(
        'res.currency',
        string='Currency',
        default=lambda self: self.env.company.currency_id,
        required=True,
    )

    next_action_required = fields.Selection(
        [
            ('yes', 'Yes'),
            ('no', 'No'),
        ],
        string='Next Action Required',
        tracking=True,
        help='Is there a follow-up action required?',
    )

    notes = fields.Text(
        string='Visit Notes',
        tracking=True,
    )

    next_action = fields.Text(
        string='Next Action',
        tracking=True,
    )

    internal_notes = fields.Text(
        string='Internal Notes',
        tracking=True,
        help='Internal notes visible only to company employees',
    )

    client_remarks = fields.Text(
        string='Client Remarks',
        tracking=True,
        help='Remarks or feedback from the client',
    )

    activity_type_id = fields.Many2one('mail.activity.type', 'Next Activity Type')

    followup_activity_id = fields.Many2one(
        'mail.activity',
        string='Follow-up Activity',
        readonly=True,
        copy=False,
    )
    next_activity_date = fields.Date('Next Activity Date')

    expense_line = fields.One2many('crm.property.visit.expense.line', 'visit_id', 'Expenses', tracking=True)

    def action_view_attachments(self):
        """Open all attachments for this visit."""
        self.ensure_one()

        # Collect all attachment IDs from all categories
        all_attachment_ids = (
            self.photo_ids.ids +
            self.document_ids.ids +
            self.signed_form_ids.ids +
            self.visiting_card_ids.ids
        )

        return {
            'name': _('Visit Attachments'),
            'type': 'ir.actions.act_window',
            'res_model': 'ir.attachment',
            'view_mode': 'tree,form',
            'domain': [('id', 'in', all_attachment_ids)],
            'context': {
                'default_res_model': 'crm.client.visit',
                'default_res_id': self.id,
            },
        }

    @api.depends('photo_ids', 'document_ids', 'signed_form_ids', 'visiting_card_ids')
    def _compute_attachment_counts(self):
        for visit in self:
            visit.photo_count = len(visit.photo_ids)
            visit.document_count = len(visit.document_ids)
            visit.signed_form_count = len(visit.signed_form_ids)
            visit.visiting_card_count = len(visit.visiting_card_ids)
            visit.total_attachment_count = (
                    visit.photo_count +
                    visit.document_count +
                    visit.signed_form_count +
                    visit.visiting_card_count
            )

    def _action_send_message(self, body):
        self.lead_id.message_post(
            body=body,
            message_type='notification',
            subtype_xmlid='mail.mt_comment',
            body_is_html=True
        )

    def action_cancel(self):
        if self.state == 'completed':
            raise UserError(_("Completed Schedule can't be canceled!"))
        body = (
            f"Property Visit\n"
            f'<span class="o-mail-Message-trackingNew me-1 fw-bold text-info">{self.name}</span> has been <span class="text-danger me-1 fw-bold">Canceled</span>'
        )
        self.state = 'cancelled'
        self._action_send_message(body)

    def action_confirm(self):
        try:
            for visit in self:
                if visit.lead_id:
                    # Colored link to visit record
                    body = (
                        f"Property Visit\n"
                        f'<span class="o-mail-Message-trackingNew me-1 fw-bold text-info">{visit.name}</span> has been <span class="text-success me-1 fw-bold">Confirmed</span> and scheduled for <span class="o-mail-Message-trackingNew me-1 fw-bold text-info">{visit.visit_date}</span>'
                    )
                    visit._action_send_message(body)
                self.state = 'planned'

        except Exception as e:
            _logger.error(e)

    def action_complete(self):
        if not self.note:
            raise UserError(_("Please Write a note before completing!"))
        if self.lead_id:
            # Colored link to visit record
            body = (
                f"Property Visit\n"
                f'<span class="o-mail-Message-trackingNew me-1 fw-bold text-info">{self.name}</span> has been <span class="text-success me-1 fw-bold">Completed</span> on <span class="o-mail-Message-trackingNew me-1 fw-bold text-info">{self.visit_date}</span>'
            )
            self._action_send_message(body)
        self.state = 'completed'

    def action_draft(self):
        try:
            for visit in self:
                if visit.lead_id:
                    body = (
                        f"Property Visit\n"
                        f'<span class="o-mail-Message-trackingNew me-1 fw-bold text-info">{visit.name}</span> has been <span class="text-warning me-1 fw-bold">Reset to Draft</span> </span>'
                    )
                    visit._action_send_message(body)
                visit.state = 'draft'

        except Exception as e:
            _logger.error(e)

    def action_re_schedule(self):
        self.ensure_one()
        return {
            'name': 'Reschedule visit',
            'model': 'ir.actions.act_window',
            'type': 'ir.actions.act_window',
            'res_model': 'property.visit.reschedule.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_visit_id': self.id,
                'default_lead_id': self.lead_id.id,
            }
        }

    # ------------------------------------------------------------
    # Sequences
    # ------------------------------------------------------------

    @api.model_create_multi
    def create(self, vals_list):
        visits = super().create(vals_list)
        for visit in visits:
            # Assign sequence if needed
            if visit.name and visit.name.lower() == 'new':
                visit.name = self.env['ir.sequence'].next_by_code('crm.property.visit')
        return visits

    def _create_next_activity(self):
        self.ensure_one()
        if self.next_action_required == 'no' or self.followup_activity_id:
            return

        summary = _('Client Visit: %s') % (self.name)
        res_model_id = self.env['ir.model']._get_id('crm.lead')
        activity = self.env['mail.activity'].sudo().create({
            'res_model_id': res_model_id,
            'res_id': self.lead_id.id,
            'activity_type_id': self.activity_type_id.id if self.activity_type_id else False,
            'summary': summary,
            'user_id': self.user_id.id,
            'note': self.next_action,
            'date_deadline': self.next_activity_date
        })
        if activity:
            self.followup_activity_id = activity.id

    def write(self, vals):
        # Fix typo 'leda_id' -> 'lead_id'
        res = super().write(vals)
        self._create_next_activity()
        if 'lead_id' in vals:
            for visit in self:
                if visit.lead_id:
                    visit.lead_id.visit_id = visit.id
        return res
    # ------------------------------------------------------------
    # Constraints
    # ------------------------------------------------------------

    @api.constrains('visit_start_time', 'visit_end_time', 'visit_date')
    def _check_visit_time(self):
        for record in self:
            if record.visit_date:
                if record.visit_start_time and record.visit_date < record.visit_start_time.date():
                    raise ValidationError(
                        "Visit Date cannot be before Visit Start Time."
                    )
                if record.visit_date < fields.Date.today():
                    raise ValidationError(
                        "Invalid Visit Date.\nVisit can't be in the past."
                    )
            if record.visit_start_time and record.visit_end_time:
                if record.visit_start_time >= record.visit_end_time:
                    raise ValidationError(
                        "Visit end time must be later than start time."
                    )

    @api.onchange('visit_date')
    def _onchange_visit_date(self):
        if self.visit_date:
            if self.visit_start_time:
                # Keep time but set new date
                self.visit_start_time = self.visit_start_time.replace(
                    year=self.visit_date.year,
                    month=self.visit_date.month,
                    day=self.visit_date.day
                )
            if self.visit_end_time:
                self.visit_end_time = self.visit_end_time.replace(
                    year=self.visit_date.year,
                    month=self.visit_date.month,
                    day=self.visit_date.day
                )

    @api.depends('visit_start_time', 'visit_end_time')
    def _compute_duration(self):
        for record in self:
            if record.visit_start_time and record.visit_end_time:
                delta = record.visit_end_time - record.visit_start_time
                # duration in hours
                record.duration = delta.total_seconds() / 3600.0
            else:
                record.duration = 0.0