from odoo import models, fields, api


class PropertyProject(models.Model):
    _name = 'property.project'
    _description = 'Property Project'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(
        string='Project Name',
        required=True,
        tracking=True
    )

    project_code = fields.Char(
        string='Project Code',
        readonly=True,
        copy=False
    )

    project_type = fields.Selection([
        ('rental', 'Rental'),
        ('sales', 'Sales'),
        ('mixed', 'Mixed'),
        ('facility', 'Facility Management'),
    ], string='Project Type', required=True, tracking=True)

    project_category = fields.Selection([
        ('residential', 'Residential'),
        ('commercial', 'Commercial'),
        ('industrial', 'Industrial'),
        ('mixed_use', 'Mixed-use'),
    ], string='Project Category', required=True)

    state = fields.Selection([
        ('planning', 'Planning'),
        ('active', 'Active'),
        ('on_hold', 'On Hold'),
        ('completed', 'Completed'),
    ], string='Status', default='planning', tracking=True)

    owner_id = fields.Many2one(
        'res.partner',
        string='Property Owner'
    )

    company_id = fields.Many2one(
        'res.company',
        default=lambda self: self.env.company
    )

    active = fields.Boolean(default=True)

    # Related Properties
    property_ids = fields.One2many(
        'property.property',
        'property_project_id',
        string='Properties'
    )

    property_count = fields.Integer(
        string='Property Count',
        compute='_compute_property_count',
        store=True
    )

    @api.depends('property_ids')
    def _compute_property_count(self):
        for project in self:
            project.property_count = len(project.property_ids)

    def create(self, vals):
        if not vals.get('project_code'):
            vals['project_code'] = self.env['ir.sequence'].next_by_code(
                'property.project'
            ) or 'NEW'
        return super().create(vals)

    def action_activate(self):
        """Set project state to Active"""
        self.write({'state': 'active'})
        return True

    def action_complete(self):
        """Set project state to Completed"""
        self.write({'state': 'completed'})
        return True

    def action_set_on_hold(self):
        """Set project state to On Hold"""
        self.write({'state': 'on_hold'})
        return True

    def action_set_planning(self):
        """Set project state to Planning"""
        self.write({'state': 'planning'})
        return True

    def action_view_properties(self):
        """View properties linked to this project"""
        self.ensure_one()
        return {
            'name': 'Properties',
            'type': 'ir.actions.act_window',
            'res_model': 'property.property',
            'view_mode': 'tree,form',
            'domain': [('property_project_id', '=', self.id)],
            'context': {'default_property_project_id': self.id}
        }

