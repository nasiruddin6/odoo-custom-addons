from odoo import fields, models, api
class MaintenanceRequest(models.Model):
    _inherit = 'maintenance.request'
    _description = 'Property Maintenance'
    # Property Related Fields
    unit_id = fields.Many2one('property.unit', string='Unit', tracking=True, required=False)
    property_id = fields.Many2one('property.property', string='Property', 
                                  related='unit_id.property_id', store=True, readonly=True)
    contract_id = fields.Many2one('property.contract', string='Contract', tracking=True)
    partner_id = fields.Many2one('res.partner', string='Tenant', tracking=True,
                                domain="[('partner_type', '=', 'tenant')]")
    landlord_id = fields.Many2one('res.partner', string='Landlord', 
                                  related='unit_id.landlord_id', store=True)
    # Maintenance Details
    maintenance_type = fields.Selection(selection_add =[
        ('repair', 'Repair'),
        ('preventive', 'Preventive'),
        ('inspection', 'Inspection'),
        ('emergency', 'Emergency'),
        ('improvement', 'Improvement'),
    ], string='Maintenance Type', default='repair', tracking=True)
    priority = fields.Selection([
        ('0', 'Low'),
        ('1', 'Normal'),
        ('2', 'High'),
        ('3', 'Very High'),
    ], string='Priority', default='1', tracking=True)
    # Location Details
    location_details = fields.Text(string='Location Details',
                                   help='Specific location within the property/unit')
    # Cost & Billing
    estimated_cost = fields.Monetary(string='Estimated Cost', currency_field='currency_id')
    actual_cost = fields.Monetary(string='Actual Cost', currency_field='currency_id')
    currency_id = fields.Many2one('res.currency', string='Currency',
                                  default=lambda self: self.env.company.currency_id)
    # Responsibility
    responsible_party = fields.Selection([
        ('landlord', 'Landlord'),
        ('tenant', 'Tenant'),
        ('shared', 'Shared'),
    ], string='Responsible Party', default='landlord', tracking=True)
    # Vendor/Service Provider
    vendor_id = fields.Many2one('res.partner', string='Service Provider/Vendor',
                                domain="[('supplier_rank', '>', 0)]")
    vendor_invoice_id = fields.Many2one('account.move', string='Vendor Invoice',
                                        domain="[('move_type', '=', 'in_invoice')]")
    # Images & Documentation
    before_images = fields.Many2many('ir.attachment', 'maintenance_request_before_images_rel',
                                     'request_id', 'attachment_id',
                                     string='Before Images')
    after_images = fields.Many2many('ir.attachment', 'maintenance_request_after_images_rel',
                                    'request_id', 'attachment_id',
                                    string='After Images')
    # Additional Info
    is_warranty = fields.Boolean(string='Under Warranty')
    warranty_details = fields.Text(string='Warranty Details')
    recurring_maintenance = fields.Boolean(string='Recurring Maintenance')
    next_maintenance_date = fields.Date(string='Next Maintenance Date')
    # Company
    company_id = fields.Many2one('res.company', string='Company',
                                default=lambda self: self.env.company)
    @api.onchange('contract_id')
    def _onchange_contract_id(self):
        """Auto-populate fields based on selected contract"""
        if self.contract_id:
            self.unit_id = self.contract_id.unit_id
            self.partner_id = self.contract_id.partner_id
