from odoo import fields, models, api

class PropertyAgreementTemplate(models.Model):
    _name = 'property.agreement.template'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Property Agreement Template'

    name = fields.Char(string='Template Name', required=True)
    content = fields.Text(string='Content', required=True)
    active = fields.Boolean(string='Active', default=True)

    @api.model_create_multi
    def create(self, vals):
        if 'name' in vals:
            vals['name'] = vals['name'].strip()
        return super(PropertyAgreementTemplate, self).create(vals)

    def write(self, vals):
        if 'name' in vals:
            vals['name'] = vals['name'].strip()
        return super(PropertyAgreementTemplate, self).write(vals)