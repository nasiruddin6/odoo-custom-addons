from odoo import models, fields, api
from odoo.exceptions import ValidationError

AVAILABLE_PRIORITIES = [
    ('0', 'Low'),
    ('1', 'Medium'),
    ('2', 'High'),
    ('3', 'Very High'),
]

class CrmPropertyVisit(models.Model):
    _name = 'crm.property.visit'
    _description = 'CRM Property Visit Schedule'
    _order = 'priority asc'

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

    state = fields.Selection([
        ('draft', 'Draft'),
        ('planned', 'Planned'),
        ('completed', 'Completed'),
        ('re_scheduled', 'Re Scheduled'),
        ('cancelled', 'Cancelled'),
    ], string="Status", default='draft', required=True)

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
    partner_id = fields.Many2one('res.partner', string="Client", related="lead_id.partner_id")
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

            # Link to the lead
            if visit.lead_id:
                visit.lead_id.visit_id = visit.id
        return visits

    def write(self, vals):
        # Fix typo 'leda_id' -> 'lead_id'
        res = super().write(vals)
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