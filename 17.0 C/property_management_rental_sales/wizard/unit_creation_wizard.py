from odoo import fields, models, api

class UnitCreation(models.TransientModel):
    _name = 'unit.creation.wizard'
    _description = 'Unit Creation Wizard'

    property_id = fields.Many2one('property.property', string='Property', required=True)
    unit_prefix = fields.Char(string='Unit Prefix', required=True, default='Unit')
    starting_number = fields.Integer(string='Starting Number', required=True, default=1)
    total_floor = fields.Integer(string='Total Floors', required=True, default=1)
    unit_per_floor = fields.Integer(string='Units per Floor', required=True, default=1)
    total_unit = fields.Integer(string='Total Units', compute='_compute_total_unit')

    @api.depends('total_floor', 'unit_per_floor')
    def _compute_total_unit(self):
        for record in self:
            record.total_unit = (record.total_floor or 0) * (record.unit_per_floor or 0)

    def create_units(self):
        """
        Create units for the selected property according to the wizard configuration.
        Returns an action that opens the created units (list or single form).
        """
        self.ensure_one()
        Unit = self.env['property.unit']
        created_ids = []
        num = self.starting_number or 1
        for floor in range(1, (self.total_floor or 0) + 1):
            for u in range(0, (self.unit_per_floor or 0)):
                name = f"{self.unit_prefix}-{num}"
                vals = {
                    'name': f"{self.property_id.name} Unit-{num}",
                    'code': name,
                    'property_id': self.property_id.id,
                    'landlord_id': self.property_id.landlord_id.id,
                    'street': self.property_id.street,
                    'street2': self.property_id.street2,
                    'city': self.property_id.city,
                    'state_id': self.property_id.state_id.id,
                    'zip': self.property_id.zip,
                    'country_id': self.property_id.country_id.id,
                    'city_id': self.property_id.city_id.id,
                    'property_for': self.property_id.property_for,
                }
                unit = Unit.create(vals)
                created_ids.append(unit.id)
                num += 1

        if not created_ids:
            # Nothing created, just close the wizard
            return {'type': 'ir.actions.act_window_close'}

        # Open the created units: if single, open form, else open list of created
        action = {
            'name': 'Created Units',
            'type': 'ir.actions.act_window',
            'res_model': 'property.unit',
            'view_mode': 'tree,form,kanban',
            'domain': [('id', 'in', created_ids)],
            'context': {'default_property_id': self.property_id.id},
            'target': 'current',
        }
        if len(created_ids) == 1:
            # Open the form view directly for the single created unit
            try:
                form_view = self.env.ref('property_management_rental_sales.view_property_unit_form')
                action['views'] = [(form_view.id, 'form')]
            except Exception:
                pass
            action.update({'res_id': created_ids[0], 'view_mode': 'form'})
        return action
