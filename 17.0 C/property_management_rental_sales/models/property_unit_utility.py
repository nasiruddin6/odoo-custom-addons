from odoo import fields, models, api

class UnitCategory(models.Model):
    _name = 'unit.category'
    _description = 'Property Unit Category'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'name asc'

    name = fields.Char(string='Category Name', required=True, tracking=True)
    code = fields.Char(string='Category Code', required=True, tracking=True)
    description = fields.Text(string='Description')
    active = fields.Boolean(string='Active', default=True)
    color = fields.Integer(string='Color Index')

    # Statistics
    unit_count = fields.Integer(string='Units', compute='_compute_unit_count')

    @api.depends('name')
    def _compute_unit_count(self):
        for record in self:
            record.unit_count = self.env['property.unit'].search_count([
                ('unit_category', '=', record.id)
            ])

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if 'name' in vals:
                vals['name'] = vals['name'].strip()
            if 'code' in vals:
                vals['code'] = vals['code'].strip().upper()
        return super(UnitCategory, self).create(vals_list)

    def write(self, vals):
        if 'name' in vals:
            vals['name'] = vals['name'].strip()
        if 'code' in vals:
            vals['code'] = vals['code'].strip().upper()
        return super(UnitCategory, self).write(vals)
