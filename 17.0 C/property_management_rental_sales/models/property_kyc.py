from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class PropertyKYC(models.Model):
    _name = 'property.kyc'
    _description = 'Property KYC Form'
    _rec_name = 'full_name'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    # 1. Applicant Information
    full_name = fields.Char(string='Full Name (as per ID)', required=True)
    parent_name = fields.Char(string="Father's / Mother's Name")
    date_of_birth = fields.Date(string='Date of Birth')
    nationality = fields.Char(string='Nationality')
    marital_status = fields.Selection([
        ('single', 'Single'),
        ('married', 'Married'),
        ('other', 'Other')
    ], string='Marital Status')

    # 2. Contact Details
    mobile_number = fields.Char(string='Mobile Number')
    email_address = fields.Char(string='Email Address')
    current_address = fields.Text(string='Current Address')
    permanent_address = fields.Text(string='Permanent Address')

    # 3. Identification Details (KYC)
    id_type = fields.Selection([
        ('national_id', 'National ID'),
        ('passport', 'Passport'),
        ('driving_license', 'Driving License')
    ], string='ID Type')
    id_number = fields.Char(string='ID Number')
    issuing_authority = fields.Char(string='Issuing Country / Authority')
    id_expiry_date = fields.Date(string='Expiry Date')

    # Documents
    id_copy_front = fields.Binary(string='ID Copy (Front)', attachment=True)
    id_copy_back = fields.Binary(string='ID Copy (Back)', attachment=True)
    photograph = fields.Binary(string='Passport-size Photograph', attachment=True)

    # 4. Employment / Business Information
    occupation = fields.Selection([
        ('service', 'Service'),
        ('business', 'Business'),
        ('self_employed', 'Self-Employed'),
        ('other', 'Other')
    ], string='Occupation')
    company_name = fields.Char(string='Company / Business Name')
    designation = fields.Char(string='Designation')
    monthly_income = fields.Float(string='Monthly Income')
    annual_income = fields.Float(string='Annual Income')

    # 5. Property Details
    property_id = fields.Many2one('property.property',string='Project / Property Name')
    unit_id = fields.Many2one('property.unit', string='Unit No / Plot No')
    property_type = fields.Selection([
        ('apartment', 'Apartment'),
        ('villa', 'Villa'),
        ('commercial', 'Commercial'),
        ('plot', 'Plot')
    ], string='Property Type')
    sales_offer_reference = fields.Char(string='Sales Offer Reference')

    # 6. Source of Funds
    fund_source_salary = fields.Boolean(string='Salary / Business Income')
    fund_source_savings = fields.Boolean(string='Savings')
    fund_source_loan = fields.Boolean(string='Loan / Mortgage')
    fund_source_other = fields.Boolean(string='Other Source')
    fund_source_other_desc = fields.Char(string='Other Source Description')

    # 7. Declaration & Consent
    customer_signature = fields.Binary(string='Customer Signature', attachment=True)
    declaration_date = fields.Date(string='Declaration Date', default=fields.Date.today)

    # 8. Verification (Office Use Only)
    kyc_status = fields.Selection([
        ('pending', 'Pending'),
        ('verified', 'Verified'),
        ('rejected', 'Rejected')
    ], string='KYC Status', default='pending', tracking=True)
    verified_by = fields.Many2one('res.users', string='Verified By')
    verification_remarks = fields.Text(string='Remarks')
    verification_date = fields.Date(string='Verification Date')

    @api.model_create_multi
    def create(self, vals_list):
        res = super().create(vals_list)
        for record in res:
            if record.so_id:
                record.so_id.state = 'waiting_for_kyc'
                record.so_id.kyc_id = res.id
        return res

    def write(self, vals):
        """Auto-populate verification date and verified by when status changes to verified"""
        res = super().write(vals)
        if vals.get('kyc_status') == 'verified':
            self.write({
                'verification_date': fields.Date.today(),
                'verified_by': self.env.user.id
            })
        return res

    def action_confirm(self):
        self.ensure_one()
        if not self.so_id:
            raise ValidationError(_('No Sales Order Found!'))
        self.write({
            'kyc_status': 'verified',
            'verification_date': fields.Date.today(),
            'verified_by': self.env.user.id
        })
        self.so_id.state = 'in_agreement'

    def action_reject(self):
        self.ensure_one()
        if not self.so_id:
            raise ValidationError(_('No Sales Order Found!'))
        self.kyc_status = 'rejected'
        self.so_id.action_cancel()

    def action_reset_to_pending(self):
        self.ensure_one()
        if not self.so_id:
            raise ValidationError(_('No Sales Order Found!'))
        self.kyc_status = 'pending'
        self.verification_date = False
        self.verified_by = False
        self.so_id.action_draft()  # Use action_draft instead of action_confirm

    def action_view_contract(self):
        self.ensure_one()
        if not self.so_id:
            return
        print(self.so_id)
        return {
            'name': 'Contract',
            'type': 'ir.actions.act_window',
            'model': 'ir.actions.act_window',
            'res_model': 'sale.order',
            'view_mode': 'form',
            'target': 'current',
            'res_id': self.so_id.id
        }
