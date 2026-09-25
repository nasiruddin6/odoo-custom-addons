from odoo import fields, models, api

class PropertyDuration(models.Model):
    _name = 'property.duration'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Property Duration'

    name = fields.Char(string='Name', required=True)
    duration = fields.Integer(string='Duration', required=True, help='Duration in number of units (e.g., 3 for 3 months)', tracking=True)
    duration_unit = fields.Selection([
        ('days', 'Days'),
        ('weeks', 'Weeks'),
        ('months', 'Months'),
        ('years', 'Years')
    ], string='Duration Unit', required=True, default='months', tracking=True)
    description = fields.Text(string='Description')
    active = fields.Boolean(string='Active', default=True)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirm', 'Confirmed')
    ], 'Status', default='draft', tracking=True)

    def action_confirm_duration(self):
        for rec in self:
            rec.state = 'confirm'

    def action_set_to_draft(self):
        for rec in self:
            rec.state = 'draft'

    @api.model_create_multi
    def create(self, vals):
        if 'name' in vals:
            vals['name'] = vals['name'].strip()
        return super(PropertyDuration, self).create(vals)

    def write(self, vals):
        if 'name' in vals:
            vals['name'] = vals['name'].strip()
        return super(PropertyDuration, self).write(vals)