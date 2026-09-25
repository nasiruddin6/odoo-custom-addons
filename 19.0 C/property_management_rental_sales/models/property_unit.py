from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
from datetime import date
from dateutil.relativedelta import relativedelta

class PropertyUnit(models.Model):
    _name = 'property.unit'
    _description = 'Property Unit'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    # Basic Information
    name = fields.Char(string='Unit Name', required=True, tracking=True)
    code = fields.Char(string='Unit Code', tracking=True)
    property_id = fields.Many2one('property.property', string='Property', required=True, ondelete='cascade')

    # Unit Details
    unit_type_id = fields.Many2one('property.type', string='Unit Type')
    property_unit_type_id = fields.Many2one('property.unit.type', string='Unit Type', help='Type of the unit based on number of bedrooms')
    unit_type = fields.Selection([
        ('1BHK', '1BHK'),
        ('2BHK', '2BHK'),
        ('3BHK', '3BHK'),
        ('4BHK', '4BHK'),
        ('other', 'Other'),
    ], string='Unit Type', help='Type of the unit based on number of bedrooms')
    unit_category = fields.Many2one('unit.category', string='Unit Category')

    floor = fields.Char(string='Floor / Level')
    building = fields.Char(string='Building / Block')
    state = fields.Selection([
        ('draft', 'Draft'),
        ('available', 'Available'),
        ('booked', 'Booked'),
        ('in_sell', 'In Sale'),
        ('sold', 'Sold'),
        ('rented', 'Rented'),
        ('leased', 'Leased'),
        ('maintenance', 'Under Maintenance'),
    ], string='Status', default='draft', tracking=True)

    # Area & Measurement
    area_sqft = fields.Float(string='Area (sqft)')
    area_sqm = fields.Float(string='Area (sqm)')
    bedroom = fields.Integer(string='Bedrooms')
    living = fields.Integer(string='Living')
    dining = fields.Integer(string='Dining')
    kitchen = fields.Integer(string='Kitchen')
    bathroom = fields.Integer(string='Bathrooms')
    balcony = fields.Integer(string='Balconies')
    parking = fields.Integer(string='Parking Spaces')
    facing = fields.Selection([
        ('north', 'North'),
        ('south', 'South'),
        ('east', 'East'),
        ('west', 'West'),
        ('northeast', 'Northeast'),
        ('northwest', 'Northwest'),
        ('southeast', 'Southeast'),
        ('southwest', 'Southwest'),
    ], string='Facing Direction')
    furnishing_type = fields.Selection([
        ('unfurnished', 'Unfurnished'),
        ('semi_furnished', 'Semi-Furnished'),
        ('fully_furnished', 'Fully Furnished'),
    ], string='Furnishing Type')

    # Pricing
    rent_price = fields.Float(string='Rent Amount (Month)')
    sale_price = fields.Float(string='Sale Price')
    currency_id = fields.Many2one('res.currency', string='Currency', default=lambda self: self.env.company.currency_id)
    property_for = fields.Selection([
        ('rent', 'For Rent'),
        ('lease', 'For Lease'),
        ('sale', 'For Sale'),
    ], string="Property For", default='rent')

    # Tenant / Owner
    landlord_id = fields.Many2one('res.partner', string='Landlord', domain=[('partner_type', '=', 'landlord')])
    partner_domain = fields.Char('Partner Domain', compute='_get_partner_domain')
    partner_id = fields.Many2one('res.partner', string='Tenant')
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company)

    # Owner / Business owner fields (added)
    owner_partner_id = fields.Many2one(
        'res.partner',
        string='Owner (Partner)',
        ondelete='restrict',
        help='Partner representing the business owner of this unit',
    )
    owner_name = fields.Char(related='owner_partner_id.name', string='Owner Name', store=True)
    owner_email = fields.Char(related='owner_partner_id.email', string='Owner Email', store=True)
    owner_phone = fields.Char(related='owner_partner_id.phone', string='Owner Phone', store=True)
    owner_street = fields.Char(related='owner_partner_id.street', string='Owner Street', store=True)
    owner_street2 = fields.Char(related='owner_partner_id.street2', string='Owner Street2', store=True)
    owner_city = fields.Char(related='owner_partner_id.city', string='Owner City', store=True)
    owner_zip = fields.Char(related='owner_partner_id.zip', string='Owner Zip', store=True)
    owner_state_id = fields.Many2one('res.country.state', related='owner_partner_id.state_id', string='Owner State', store=True)
    owner_country_id = fields.Many2one('res.country', related='owner_partner_id.country_id', string='Owner Country', store=True)
    owner_vat = fields.Char(related='owner_partner_id.vat', string='Owner VAT', store=True)
    owner_is_company = fields.Boolean(related='owner_partner_id.is_company', string='Owner is a Company', store=True)

    owner_company_registration = fields.Char(string='Owner Registration No.')
    owner_notes = fields.Text(string='Owner Notes')

    # Address
    street = fields.Char(string='Street')
    street2 = fields.Char(string='Street 2')
    city = fields.Char(string='City')
    state_id = fields.Many2one('res.country.state', string='State')
    country_id = fields.Many2one('res.country', string='Country')
    zip = fields.Char(string='ZIP')
    latitude = fields.Float(string='Latitude')
    longitude = fields.Float(string='Longitude')
    city_id = fields.Many2one('property.city', string='City')

    # Additional Details
    construction_year = fields.Char(string='Construction Year')
    availability_date = fields.Date(string='Availability Date')
    description = fields.Html(string='Description')
    image_1024 = fields.Image(string='Image 1024', max_width=1024, max_height=1024)

    # Relations
    amenity_ids = fields.Many2many('property.amenities', string='Amenities')
    specification_ids = fields.Many2many('property.specification', string='Specifications')
    connectivity_ids = fields.Many2many('property.connectivity', string='Nearby Connectivity')
    contract_ids = fields.One2many('property.contract', 'unit_id', string='Contracts')
    contract_count = fields.Integer(string='Contract Count', compute='_compute_contract_count')
    sales_contract_ids = fields.One2many('property.contract', 'unit_id', string='Sales Contracts')
    sales_contract_count = fields.Integer(string='Sales Contract Count', compute='_compute_contract_count')
    maintenance_request_ids = fields.One2many('maintenance.request', 'unit_id', string='Maintenance Requests')

    # Computed / Smart Fields

    maintenance_request_count = fields.Integer(string='Maintenance Count', compute='_compute_maintenance_request_count')
    is_available = fields.Boolean(string='Is Available', compute='_compute_is_available')
    has_owner = fields.Boolean(string='Has Owner', compute='_compute_has_owner')

    @api.depends('property_for')
    def _get_partner_domain(self):
        for rec in self:
            domain = []
            if rec.property_for in ['rent', 'lease']:
                domain.append(('partner_type', '=', 'tenant'))
            elif rec.property_for == 'sale':
                domain.append(('partner_type', '=', 'customer'))
            rec.partner_domain = domain

    @api.onchange('property_unit_type_id')
    def _action_unit_change(self):
        if self.property_unit_type_id:
            self.write({
                'bedroom': self.property_unit_type_id.bedroom,
                'living': self.property_unit_type_id.living,
                'dining': self.property_unit_type_id.dining,
                'kitchen': self.property_unit_type_id.kitchen,
                'bathroom': self.property_unit_type_id.bathroom,
                'balcony': self.property_unit_type_id.balcony,
                'parking': self.property_unit_type_id.parking,
            })

    def _compute_contract_count(self):
        for unit in self:
            unit.contract_count = len(unit.contract_ids)
            unit.sales_contract_count = self.env['sale.order'].search_count([('unit_id', '=', unit.id), ('is_spa', '=', True)])

    def _compute_maintenance_request_count(self):
        for unit in self:
            unit.maintenance_request_count = self.env['maintenance.request'].search_count([('unit_id', '=', unit.id)])

    @api.depends('state')
    def _compute_is_available(self):
        for rec in self:
            rec.is_available = rec.state == 'available'

    @api.depends('owner_partner_id')
    def _compute_has_owner(self):
        for rec in self:
            rec.has_owner = bool(rec.owner_partner_id)

    @api.model_create_multi
    def create(self, vals):
        if 'name' in vals:
            vals['name'] = vals['name'].strip()
        return super(PropertyUnit, self).create(vals)

    def write(self, vals):
        if 'name' in vals:
            vals['name'] = vals['name'].strip()
        return super(PropertyUnit, self).write(vals)

    def action_view_contracts(self):
        self.ensure_one()
        action = self.env['ir.actions.act_window']._for_xml_id('property_management_rental_sales.action_property_renting_contract')
        action['domain'] = [('unit_id', '=', self.id)]
        action['context'] = {
            'default_unit_id': self.id,
            'default_contract_value': self.rent_price,
            'default_partner_id': self.partner_id.id,
        }
        if self.contract_count == 1:
            action['res_id'] = self.contract_ids[0].id
            action['view_mode'] = 'form'
        return action

    def action_view_sales_contracts(self):
        self.ensure_one()
        action = self.env['ir.actions.act_window']._for_xml_id('property_management_rental_sales.action_property_sales_contract')
        action['domain'] = [('unit_id', '=', self.id)]
        action['context'] = {'default_unit_id': self.id}
        if self.contract_count == 1:
            action['res_id'] = self.sales_contract_ids[0].id
            action['view_mode'] = 'form'
        return action

    def action_view_maintenance_requests(self):
        self.ensure_one()
        return {
            'name': 'Maintenance Requests',
            'type': 'ir.actions.act_window',
            'res_model': 'maintenance.request',
            'view_mode': 'list,form',
            'domain': [('unit_id', '=', self.id)],
            'context': {
                'default_unit_id': self.id,
                'default_unit_id': self.id,
                'default_property_id': self.property_id.id,
            }
        }

    def set_available(self):
        for unit in self:
            if not unit.property_unit_type_id:
                raise UserError('Please set the Unit Type before making the unit available.')
            unit.state = 'available'

    def action_to_draft(self):
        for unit in self:
            unit.state = 'draft'

    def create_new_contract(self):
        """Create a rent contract for this unit.

        Preconditions:
        - The unit must have a tenant assigned (`partner_id`).

        The method creates a `property.contract` record, an initial
        `property.invoice` for the first rent, sets the unit state to
        'rented', and returns an action opening the contract form view.
        """

        if self.property_for in ('rent', 'lease'):
            return self.create_rent_contract()
        elif self.property_for == 'sale':
            return self.create_sell_contract()
        else:
            raise UserError('Property For must be set to Rent, Lease, or Sale to create a contract.')

    def create_rent_contract(self):
        self.ensure_one()
        if not self.partner_id:
            raise UserError('Please set a Tenant/Customer on the unit before creating a contract.')
        contract = self.env['property.contract']

        duration = self.env['property.duration'].sudo().search([], limit=1, order="id asc")
        if not duration:
            raise ValidationError(_("Please create a Duration first!"))

        # Default dates: start today, end after 1 year
        start_date = date.today()
        end_date = start_date + relativedelta(years=1)

        contract_vals = {
            'start_date': start_date,
            'end_date': end_date,
            'contract_value': self.rent_price or 0.0,
            'partner_id': self.partner_id.id,
            'property_id': self.property_id.id,
            'unit_id': self.id,
            'company_id': (self.company_id and self.company_id.id) or self.env.company.id,
            'invoice_start_date': start_date,
            'sale_price': 0.0,
            'duration_id': duration.id
        }

        contract = contract.create(contract_vals)

        # Open the created contract in form view
        action = {
            'name': 'Contract',
            'type': 'ir.actions.act_window',
            'res_model': 'property.contract',
            'res_id': contract.id,
            'view_mode': 'form',
        }
        try:
            form_view = self.env.ref('property_management_rental_sales.property_contract_view_form')
            action['views'] = [(form_view.id, 'form')]
        except Exception:
            pass
        return action

    def create_sell_contract(self):
        self.ensure_one()

        if not self.sale_price or self.sale_price <= 0:
            raise UserError('Please set a valid Sale Price on the unit before creating a sale contract.')

        # Validate that a customer is assigned
        if not self.partner_id:
            raise UserError('Please set a Customer/Tenant on the unit before creating a sale contract.')

        # Get the rental installment product from settings
        installment_product_id = int(self.env['ir.config_parameter'].sudo().get_param(
            'property_management_rental_sales.sales_installment_product_id', 0
        ))

        if not installment_product_id:
            raise UserError('Please configure the Default Rental Product in Settings.')

        installment_product = self.env['product.product'].browse(installment_product_id)
        if not installment_product.exists():
            raise UserError('The configured Rental Product no longer exists. Please update Settings.')

        price = self.sale_price or 0.0

        order_line = [(0, 0, {
            'product_id': installment_product.id,
            'name': installment_product.name,
            'product_uom_qty': 1,
            'price_unit': price,
        })]

        sale_order_vals = {
            'partner_id': self.partner_id.id,
            'order_line': order_line,
            'property_id': self.property_id.id,
            'unit_id': self.id,
            'state': 'draft',
            'is_spa': True
        }

        sale_order = self.env['sale.order'].create(sale_order_vals)
        self.write({'state': 'in_sell'})

        return {
            'name': 'Sale Order',
            'type': 'ir.actions.act_window',
            'res_model': 'sale.order',
            'view_mode': 'form',
            'res_id': sale_order.id,
            'target': 'current',
        }

    def action_create_maintenance_request(self):
        self.ensure_one()

        action = self.env.ref('maintenance.hr_equipment_request_action').sudo().read()[0]
        form_view = self.env.ref('maintenance.hr_equipment_request_view_form')

        action.update({
            'views': [(form_view.id, 'form')],
            'target': 'current',
            'context': {
                **self.env.context,
                'default_unit_id': self.id,
                'default_property_id': self.property_id.id if self.property_id else False,
                'default_landlord_id': self.landlord_id.id if self.landlord_id else False,
                'default_partner_id': self.partner_id.id if self.partner_id else False,
            },
        })
        return action

