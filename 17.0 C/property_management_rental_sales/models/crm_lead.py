from odoo import fields, models, api
from odoo.exceptions import UserError

class CrmLead(models.Model):
    _inherit = 'crm.lead'
    _description = 'Lead'

    # Existing Fields
    unit_id = fields.Many2one('property.unit', string='Unit', tracking=True)
    property_id = fields.Many2one('property.property', string='Property', tracking=True)
    contract_ids = fields.One2many('property.contract', 'lead_id', string='Contracts')
    contract_count = fields.Integer(string="Contract Count", compute='_compute_contract_count')
    
    # Property Confirmation Workflow Fields
    interested_property_ids = fields.Many2many('property.unit', string='Interested Properties', tracking=True)

    # PAGE 1: Client Property Requirement Details
    requirement_type = fields.Selection([
        ('sale', 'Buy'),
        ('rent', 'Rent'),
    ], string='Requirement Type', tracking=True)
    property_category = fields.Selection([
        ('residential', 'Residential'),
        ('commercial', 'Commercial'),
        ('industrial', 'Industrial'),
        ('mixed_use', 'Mixed Use'),
    ], string='Property Category', tracking=True)
    property_type = fields.Selection([
        ('apartment', 'Apartment'),
        ('villa', 'Villa'),
        ('townhouse', 'Townhouse'),
        ('studio', 'Studio'),
        ('penthouse', 'Penthouse'),
        ('office', 'Office'),
        ('retail', 'Retail'),
        ('warehouse', 'Warehouse'),
    ], string='Property Type', tracking=True)
    purpose = fields.Selection([
        ('personal_residence', 'Personal Residence'),
        ('investment', 'Investment'),
        ('corporate', 'Corporate'),
        ('commercial_business', 'Commercial Business'),
        ('rental_income', 'Rental Income'),
    ], string='Purpose', tracking=True)
    preferred_location_ids = fields.Many2many('property.city', string='Preferred Locations')
    min_area = fields.Float(string='Minimum Area (Sqft)', tracking=True)
    max_area = fields.Float(string='Maximum Area (Sqft)', tracking=True)
    bedroom_count = fields.Integer(string='Bedroom Count', tracking=True)
    bathroom_count = fields.Integer(string='Bathroom Count', tracking=True)
    floor_preference = fields.Selection([
        ('ground', 'Ground Floor'),
        ('lower_mid', 'Lower Mid'),
        ('mid', 'Mid'),
        ('upper_mid', 'Upper Mid'),
        ('top', 'Top Floor'),
        ('any', 'Any'),
    ], string='Floor Preference', tracking=True)
    facing = fields.Selection([
        ('north', 'North'),
        ('south', 'South'),
        ('east', 'East'),
        ('west', 'West'),
        ('northeast', 'North-East'),
        ('northwest', 'North-West'),
        ('southeast', 'South-East'),
        ('southwest', 'South-West'),
    ], string='Facing', tracking=True)
    furnishing_status = fields.Selection([
        ('unfurnished', 'Unfurnished'),
        ('semi_furnished', 'Semi-Furnished'),
        ('furnished', 'Furnished'),
        ('luxury_furnished', 'Luxury Furnished'),
    ], string='Furnishing Status', tracking=True)

    # PAGE 2: Budget & Financial Details
    budget_min = fields.Monetary(string='Minimum Budget', currency_field='currency_id', tracking=True)
    budget_max = fields.Monetary(string='Maximum Budget', currency_field='currency_id', tracking=True)
    currency_id = fields.Many2one('res.currency', string='Currency', default=lambda self: self.env.company.currency_id)
    payment_mode = fields.Selection([
        ('cash', 'Cash'),
        ('cheque', 'Cheque'),
        ('bank_transfer', 'Bank Transfer'),
        ('loan', 'Loan'),
        ('installment', 'Installment'),
        ('combination', 'Combination'),
    ], string='Payment Mode', tracking=True)
    loan_required = fields.Boolean(string='Loan Required', tracking=True)
    bank_id = fields.Many2one('res.bank', string='Preferred Bank', tracking=True)
    booking_amount = fields.Monetary(string='Booking Amount', currency_field='currency_id', tracking=True)
    expected_roi = fields.Float(string='Expected ROI (%)', help='Expected Return on Investment', tracking=True)

    # PAGE 3: Rental-Specific Information
    lease_duration = fields.Selection([
        ('3_months', '3 Months'),
        ('6_months', '6 Months'),
        ('1_year', '1 Year'),
        ('2_years', '2 Years'),
        ('3_years', '3 Years'),
        ('5_years', '5 Years'),
        ('flexible', 'Flexible'),
    ], string='Lease Duration', tracking=True)
    move_in_date = fields.Date(string='Move-In Date', tracking=True)
    rent_frequency = fields.Selection([
        ('monthly', 'Monthly'),
        ('quarterly', 'Quarterly'),
        ('semi_annual', 'Semi-Annual'),
        ('annual', 'Annual'),
    ], string='Rent Frequency', tracking=True)
    security_deposit_budget = fields.Monetary(string='Security Deposit Budget', currency_field='currency_id', tracking=True)
    maintenance_budget = fields.Monetary(string='Maintenance Budget', currency_field='currency_id', tracking=True)
    tenant_type = fields.Selection([
        ('individual', 'Individual'),
        ('family', 'Family'),
        ('corporate', 'Corporate'),
        ('student', 'Student'),
    ], string='Tenant Type', tracking=True)
    furnishing_requirement = fields.Selection([
        ('unfurnished', 'Unfurnished'),
        ('semi_furnished', 'Semi-Furnished'),
        ('furnished', 'Furnished'),
    ], string='Furnishing Requirement', tracking=True)
    pets_allowed = fields.Boolean(string='Pets Allowed', tracking=True)

    # PAGE 4: Sales-Specific Information
    purchase_timeline = fields.Selection([
        ('immediate', 'Immediate'),
        ('1_3_months', '1-3 Months'),
        ('3_6_months', '3-6 Months'),
        ('6_12_months', '6-12 Months'),
        ('12_plus_months', '12+ Months'),
    ], string='Purchase Timeline', tracking=True)
    ownership_preference = fields.Selection([
        ('single', 'Single Owner'),
        ('joint', 'Joint Ownership'),
        ('company', 'Company Ownership'),
    ], string='Ownership Preference', tracking=True)
    construction_status = fields.Selection([
        ('ready', 'Ready'),
        ('under_construction', 'Under Construction'),
        ('pre_launch', 'Pre-Launch'),
    ], string='Construction Status', tracking=True)
    possession_date = fields.Date(string='Possession Date', tracking=True)
    registration_budget = fields.Monetary(string='Registration Budget', currency_field='currency_id', tracking=True)
    tax_consideration = fields.Boolean(string='Tax Consideration Required', tracking=True)

    # PAGE 5: Client Profile & Qualification
    client_type = fields.Selection([
        ('individual', 'Individual'),
        ('nri', 'NRI'),
        ('company', 'Company'),
        ('huf', 'HUF'),
        ('trust', 'Trust'),
    ], string='Client Type', tracking=True)
    nationality = fields.Selection([
        ('indian', 'Indian'),
        ('foreign', 'Foreign'),
    ], string='Nationality', tracking=True)
    id_type = fields.Selection([
        ('aadhar', 'Aadhar'),
        ('pan', 'PAN'),
        ('passport', 'Passport'),
        ('voter_id', 'Voter ID'),
        ('driving_license', 'Driving License'),
    ], string='ID Type', tracking=True)
    id_number = fields.Char(string='ID Number', tracking=True)
    employment_type = fields.Selection([
        ('salaried', 'Salaried'),
        ('self_employed', 'Self-Employed'),
        ('business', 'Business'),
        ('retired', 'Retired'),
        ('other', 'Other'),
    ], string='Employment Type', tracking=True)
    company_name = fields.Char(string='Company Name', tracking=True)
    decision_maker = fields.Boolean(string='Is Decision Maker', tracking=True)
    preferred_contact_time = fields.Selection([
        ('morning', 'Morning (9AM-12PM)'),
        ('afternoon', 'Afternoon (12PM-3PM)'),
        ('evening', 'Evening (3PM-6PM)'),
        ('anytime', 'Anytime'),
    ], string='Preferred Contact Time', tracking=True)

    # PAGE 6: Legal & Compliance
    kyc_status = fields.Selection([
        ('pending', 'Pending'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('rejected', 'Rejected'),
    ], string='KYC Status', tracking=True)
    agreement_type = fields.Selection([
        ('rental_agreement', 'Rental Agreement'),
        ('sale_deed', 'Sale Deed'),
        ('lease_agreement', 'Lease Agreement'),
        ('mou', 'MOU'),
        ('other', 'Other'),
    ], string='Agreement Type', tracking=True)
    document_status = fields.Selection([
        ('pending', 'Pending'),
        ('submitted', 'Submitted'),
        ('under_review', 'Under Review'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ], string='Document Status', tracking=True)
    compliance_notes = fields.Text(string='Compliance Notes')

    # PAGE 7: Decision & Closing Indicators
    interest_level = fields.Selection([
        ('cold', 'Cold'),
        ('warm', 'Warm'),
        ('hot', 'Hot'),
        ('very_hot', 'Very Hot'),
    ], string='Interest Level', tracking=True)
    negotiation_status = fields.Selection([
        ('not_started', 'Not Started'),
        ('in_progress', 'In Progress'),
        ('offer_made', 'Offer Made'),
        ('offer_accepted', 'Offer Accepted'),
        ('deal_closed', 'Deal Closed'),
    ], string='Negotiation Status', tracking=True)
    expected_close_date = fields.Date(string='Expected Close Date', tracking=True)
    deal_breakers = fields.Text(string='Deal Breakers')
    lost_reason_property = fields.Selection([
        ('price', 'Price Too High'),
        ('location', 'Location Not Suitable'),
        ('property_condition', 'Property Condition'),
        ('amenities', 'Missing Amenities'),
        ('legal_issues', 'Legal Issues'),
        ('financing', 'Financing Issues'),
        ('better_option', 'Found Better Option'),
        ('timing', 'Timing Issues'),
        ('other', 'Other'),
    ], string='Lost Reason (Property-Specific)', tracking=True)
    visit_schedule_count = fields.Integer('Visit Schedule Count', compute='_compute_visit_schedule_count')

    def _compute_visit_schedule_count(self):
        for rec in self:
            rec.visit_schedule_count = self.env['crm.property.visit'].sudo().search_count([
                ('lead_id', '=', rec.id)
            ])

    @api.onchange('property_id')
    def _onchange_property_id(self):
        if self.property_id:
            return {'domain': {'unit_id': [('property_id', '=', self.property_id.id)]}}
        else:
            return {'domain': {'unit_id': []}}

    @api.onchange('unit_id')
    def _onchange_unit_id(self):
        if self.unit_id:
            self.property_id = self.unit_id.property_id

    def action_create_contract(self):
        self.ensure_one()
        if not self.partner_id:
            raise UserError("Please select a customer before creating a contract.")
        if not self.unit_id:
            raise UserError("Please select a unit before creating a contract.")
        if not self.property_id:
            raise UserError("Please select a property before creating a contract.")
        if not self.requirement_type:
            raise UserError("Please specify the requirement type (Buy/Rent/Lease) before creating a contract.")
        
        vals = {
            'partner_id': self.partner_id.id,
        }
        res_model = ''
        if self.requirement_type == 'rent' and not self.unit_id.rent_price:
            vals.update({
                'rent_price': self.expected_revenue if self.expected_revenue else 0.0,
            })
            res_model = 'property.contract'

        elif self.requirement_type == 'sale' and not self.unit_id.sale_price:
            vals.update({
                'sale_price': self.expected_revenue if self.expected_revenue else 0.0,
            })
            res_model = 'sale.order'

        self.unit_id.write(vals)
        return self.unit_id.create_new_contract()

    def _compute_contract_count(self):
        for lead in self:
            lead.contract_count = len(lead.contract_ids)

    def action_view_contracts(self):
        self.ensure_one()
        return {
            'name': 'Contracts',
            'type': 'ir.actions.act_window',
            'res_model': 'property.contract',
            'view_mode': 'tree,form',
            'domain': [('lead_id', '=', self.id)],
            'context': {'default_lead_id': self.id}
        }

    def action_confirm_property(self):
        """
        Open property confirmation wizard to select and confirm a unit for this lead.
        """
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Confirm Property',
            'res_model': 'confirm.property.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_lead_id': self.id,
                'default_available_property_unit_ids': [(6, 0, self.interested_property_ids.ids)]
            }
        }

    def action_schedule_visit(self):
        """
        Schedule a new visit for this lead
        """

        return {
            'name': 'Schedule Visit',
            'type': 'ir.actions.act_window',
            'res_model': 'crm.property.visit',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_lead_id': self.id,
            }
        }

    def action_view_visits(self):
        self.ensure_one()
        visit_ids = self.env['crm.property.visit'].search([('lead_id', '=', self.id)])
        if len(visit_ids) == 1:
            return {
                'name': 'Scheduled Visit',
                'type': 'ir.actions.act_window',
                'res_model': 'crm.property.visit',
                'view_mode': 'form',
                'res_id': visit_ids.id,
                'target': 'current',
            }

        else:
            return {
                'name': 'Scheduled Visit',
                'type': 'ir.actions.act_window',
                'res_model': 'crm.property.visit',
                'view_mode': 'tree,form',
                'domain': [
                    ('lead_id', '=', self.id)
                ],
                'target': 'current',
                'context': {
                    'default_lead_id': self.id,
                }
            }