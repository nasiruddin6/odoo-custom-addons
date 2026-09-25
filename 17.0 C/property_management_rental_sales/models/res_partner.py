from odoo import fields, models, api

class ResTenant(models.Model):
    _inherit = 'res.partner'
    _description = 'Tenant'

    partner_type = fields.Selection([
        ('tenant', 'Tenant'),
        ('landlord', 'Landlord / Owner'),
        ('customer', 'Customer'),
        ('broker', 'Agent / Broker'),
        ('vendor', 'Vendor / Supplier'),
        ('contractor', 'Contractor'),
    ], string='Partner Type')
    tenant_code = fields.Char(string="Tenant Code", tracking=True)
    nationality = fields.Char(string="Nationality", tracking=True)
    profession = fields.Char(string="Profession", tracking=True)
    trade_license_no = fields.Char(string="Trade License No", tracking=True)
    license_expiry_date = fields.Date(string="License Expiry Date", tracking=True)
    visa_type = fields.Selection([
        ('visit', 'Visit Visa'),
        ('tourist', 'Tourist Visa'),
        ('employment', 'Employment Visa'),
        ('student', 'Student Visa'),
        ('residence', 'Residence Visa'),
        ('other', 'Other'),
    ], string="Visa Type", tracking=True)
    visa_expiry_date = fields.Date(string="Visa Expiry Date", tracking=True)
    po_box_number = fields.Char(string="PO Box Number", tracking=True)

    #===========================================================================================================
    # KYC Part
    #===========================================================================================================
    # 1. Applicant Information
    full_name = fields.Char(string='Full Name (as per ID)', tracking=True)
    parents_name = fields.Char(string="Father's / Mother's Name")
    date_of_birth = fields.Date(string='Date of Birth')
    nationality = fields.Char(string='Nationality', tracking=True)
    marital_status = fields.Selection([
        ('single', 'Single'),
        ('married', 'Married'),
        ('other', 'Other')
    ], string='Marital Status')

    # 3. Identification Details (KYC)
    id_type = fields.Selection([
        ('national_id', 'National ID'),
        ('passport', 'Passport'),
        ('driving_license', 'Driving License')
    ], string='ID Type', tracking=True)
    id_number = fields.Char(string='ID Number', tracking=True)
    issuing_authority = fields.Char(string='Issuing Country / Authority', tracking=True)
    id_expiry_date = fields.Date(string='Expiry Date', tracking=True)

    # Documents
    id_copy_front = fields.Binary(string='ID Copy (Front)', attachment=True)
    id_copy_back = fields.Binary(string='ID Copy (Back)', attachment=True)
    photograph = fields.Binary(string='Passport-size Photograph', attachment=True)

    # 4. Employment / Business Information
    monthly_income = fields.Float(string='Monthly Income', tracking=True)
    annual_income = fields.Float(string='Annual Income', tracking=True)

    # 6. Source of Funds
    fund_source_salary = fields.Boolean(string='Salary / Business Income', tracking=True)
    fund_source_savings = fields.Boolean(string='Savings', tracking=True)
    fund_source_loan = fields.Boolean(string='Loan / Mortgage', tracking=True)
    fund_source_other = fields.Boolean(string='Other Source', tracking=True)
    fund_source_other_desc = fields.Char(string='Other Source Description', tracking=True)
    # 7. Declaration & Consent
    customer_signature = fields.Binary(string='Customer Signature', attachment=True)
    declaration_date = fields.Date(string='Declaration Date', default=fields.Date.today)

    # 8. Verification (Office Use Only)
    kyc_status = fields.Selection([
        ('pending', 'Pending'),
        ('verified', 'Verified'),
        ('rejected', 'Rejected'),
        ('expired', 'Expired'),
    ], string='KYC Status', default='pending', tracking=True)
    verified_by = fields.Many2one('res.users', string='Verified By', tracking=True)
    verification_remarks = fields.Text(string='Remarks', tracking=True)
    verification_date = fields.Date(string='Verification Date', tracking=True)

    def action_confirm_kyc_verification(self):
        self.ensure_one()
        self.write({
            'kyc_status': 'verified',
            'verified_by': self.env.user.id,
            'verification_date': fields.Date.today()
        })

    def action_reject_kyc(self):
        self.ensure_one()
        self.kyc_status = 'rejected'

    def action_pending(self):
        self.ensure_one()
        self.kyc_status = 'pending'

    def action_expire_kyc(self):
        self.ensure_one()
        self.kyc_status = 'expired'