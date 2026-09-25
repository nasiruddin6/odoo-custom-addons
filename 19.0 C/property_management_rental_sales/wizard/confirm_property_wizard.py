from odoo import fields, models, api


class ConfirmPropertyWizard(models.TransientModel):
    _name = 'confirm.property.wizard'
    _description = 'Property Confirmation Wizard'

    lead_id = fields.Many2one('crm.lead', string='Lead', required=True)
    unit_id = fields.Many2one('property.unit', string='Unit', required=True)
    available_property_unit_ids = fields.Many2many(
        'property.unit',
        string='Available Property Units'
    )

    def action_confirm(self):
        """
        Confirm the selected property unit for the lead:
        1. Set confirmed_unit_id on the lead
        2. Add unit to interested_property_ids
        3. Close the wizard
        """
        self.ensure_one()
        if not self.unit_id:
            return {'type': 'ir.actions.act_window_close'}

        # Update the lead with confirmed unit and interested properties
        self.lead_id.write({
            'unit_id': self.unit_id.id,
            # 'interested_property_ids': [(4, self.unit_id.id)],  # Add to many2many
        })

        return {'type': 'ir.actions.act_window_close'}