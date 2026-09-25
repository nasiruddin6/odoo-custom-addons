from odoo import fields, models, api
from odoo.tools.safe_eval import safe_eval
from odoo.exceptions import ValidationError

class PropertyProperty(models.Model):
    _name = 'property.property'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Property Property'

    name = fields.Char(string='Property Name', required=True)
    code = fields.Char(string='Property Code', required=True)
    property_project_id = fields.Many2one('property.project', string='Project', tracking=True)
    property_type_id = fields.Many2one('property.type', string='Property Type')
    property_for = fields.Selection([('sale', 'For Sale'), ('rent', 'For Rent')], string='Property For', required=True)
    landlord_id = fields.Many2one('res.partner', string='Landlord', domain=[('partner_type', '=', 'landlord')])
    company_id = fields.Many2one('res.company', string='Company', required=True, default=lambda self: self.env.company)
    construction_status = fields.Selection([('ready', 'Ready to Move'), ('under_construction', 'Under Construction')], string='Construction Status', required=True)
    construction_year = fields.Char(string='Construction Year')
    date_of_listing = fields.Date(string='Date of Listing')
    brochure = fields.Binary(string='Brochure')
    property_image = fields.Image(string='Property Image', max_width=1920, max_height=1920)
    street = fields.Char(string='Street')
    street2 = fields.Char(string='Street2')
    zip = fields.Char(string='Zip')
    city = fields.Char(string='City')
    state_id = fields.Many2one('res.country.state', string='State')
    country_id = fields.Many2one('res.country', string='Country')

    latitude = fields.Float(string='Latitude', digits=(16, 5))
    longitude = fields.Float(string='Longitude', digits=(16, 5))

    total_units = fields.Integer(string='Total Units', compute='_compute_unit_count')
    area_unit_size = fields.Float(string='Area Unit Size')
    available_units = fields.Integer(string='Available Units', compute='_compute_unit_count')
    rented_units = fields.Integer(string='Rented Units', compute='_compute_unit_count')
    sold_units = fields.Integer(string='Sold Units', compute='_compute_unit_count')
    leased_units = fields.Integer(string='Leased Units', compute='_compute_unit_count')
    remaining_units = fields.Integer(string='Remaining Units', compute='_compute_unit_count')
    area_size = fields.Float(string='Area Size')
    category_id = fields.Many2one('property.category', string='Category')
    furnish_type_id = fields.Many2one('property.furnish.type', string='Furnish Type')
    city_id = fields.Many2one('property.city', string='City')
    connectivity_ids = fields.Many2many('property.connectivity', string='Connectivity Options')
    specification_ids = fields.Many2many('property.specification', string='Specifications')
    amenity_ids = fields.Many2many('property.amenities', string='Amenities')
    facility_ids = fields.Many2many('property.facilities', string='Facilities')
    tag_ids = fields.Many2many('property.tags', string='Tags')
    utility_ids = fields.Many2many('product.product', string='Utilities')
    taxes_id = fields.Many2many('account.tax', string='Taxes', default=lambda self: self._default_taxes())

    developer_id = fields.Many2one('res.partner', string='Developer')
    state = fields.Selection([
        ('new', 'New'),
        ('available', 'Available'),
        ('reserved', 'Reserved'),
        ('rented', 'Rented'),
        ('sold', 'Sold'),
        ('renovate', 'Renovation'),
        ('inactive', 'Inactive'),
        ('closed', 'Closed'),
    ], string='Status', default='new', tracking=True)
    total_area = fields.Float(string='Total Area')
    usable_area = fields.Float(string='Usable Area (ft²)')
    land_area = fields.Float(string='Land Area')
    built_up_area = fields.Float(string='Built-up Area')
    carpet_area = fields.Float(string='Carpet Area')
    currency_id = fields.Many2one(string="Currency", related='company_id.currency_id', store=True)
    property_value = fields.Monetary(string='Property Value', currency_field='currency_id')
    website_published = fields.Boolean(string='Published on Website', default=False)

    description = fields.Text(string='Description')
    active = fields.Boolean(string='Active', default=True)
    unit_ids = fields.One2many('property.unit', 'property_id', string='Units')
    unit_count = fields.Integer(string='Unit Count', compute='_compute_unit_count')

    def _default_taxes(self):
        """Get default sales tax from company settings."""
        company = self.env.company
        if company.account_sale_tax_id:
            return [(6, 0, [company.account_sale_tax_id.id])]
        return False

    def _compute_unit_count(self):
        for prop in self:
            prop.unit_count = len(prop.unit_ids)
            prop.total_units = len(prop.unit_ids)
            prop.available_units = len(prop.unit_ids.filtered(lambda u: u.state == 'available'))
            prop.rented_units = len(prop.unit_ids.filtered(lambda u: u.state == 'rented'))
            prop.sold_units = len(prop.unit_ids.filtered(lambda u: u.state == 'sold'))
            prop.leased_units = len(prop.unit_ids.filtered(lambda u: u.state == 'leased'))

    def action_view_units(self):
        return {
            'name': 'Property Units',
            'type': 'ir.actions.act_window',
            'res_model': 'property.unit',
            'view_mode': 'tree,form',
            'domain': [('property_id', '=', self.id)],
            'context': {'default_property_id': self.id}
        }

    def action_view_maintenance_requests(self):
        return {
            'name': 'Maintenance Requests',
            'type': 'ir.actions.act_window',
            'res_model': 'maintenance.request',
            'view_mode': 'tree,form',
            'domain': [('property_id', '=', self.id)],
            'context': {'default_property_id': self.id}
        }

    def create_units(self):
        """Open the unit creation wizard with defaults for this property."""
        self.ensure_one()
        action = self.env.ref('property_management_rental_sales.action_unit_creation_wizard').sudo().read()[0]

        # Helper to coerce various stored context formats into a dict safely.
        def _normalize_ctx(raw_ctx):
            # If it's already a dict, copy it
            if isinstance(raw_ctx, dict):
                return dict(raw_ctx)
            # If it's a string, try to safe_eval it (common when stored as a string in DB)
            if isinstance(raw_ctx, str):
                try:
                    evaluated = safe_eval(raw_ctx)
                    return evaluated if isinstance(evaluated, dict) else {}
                except Exception:
                    return {}
            # If it's a list/tuple, try dict(list) first (works for list of key/value pairs)
            if isinstance(raw_ctx, (list, tuple)):
                try:
                    return dict(raw_ctx)
                except Exception:
                    # Maybe it's an iterable of dicts or other items - merge dict items
                    ctx = {}
                    for item in raw_ctx:
                        if isinstance(item, dict):
                            ctx.update(item)
                    return ctx
            # Fallback: empty dict
            return {}

        raw_ctx = action.get('context', {})
        ctx = _normalize_ctx(raw_ctx)

        # Update with defaults for the wizard
        ctx.update({
            'default_property_id': self.id,
            'default_unit_prefix': f"{self.code}-U",
            'default_starting_number': (self.unit_count or 0) + 1,
            'taxes_id': [(6, 0, self.taxes_id.ids)] if self.taxes_id else False,
        })
        action['context'] = ctx
        return action

    def set_available(self):
        for record in self:
            record.state = 'available'

    def to_new(self):
        for record in self:
            record.state = 'new'

    def set_to_renovation(self):
        for record in self:
            record.state = 'renovate'

    @api.constrains('construction_year')
    def _check_construction_year(self):
        for rec in self:
            if rec.construction_year and not rec.construction_year.isdigit():
                raise ValidationError("Construction Year must contain digits only.")


    @api.onchange('city_id')
    def _onchange_city_id(self):
        if self.city_id and self.city_id.state_id:
            self.state_id = self.city_id.state_id.id
        if self.city_id and self.city_id.country_id:
            self.country_id = self.city_id.country_id.id
        self.city = self.city_id.name if self.city_id else False
