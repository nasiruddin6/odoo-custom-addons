from odoo import api, models, fields, _


class RegistrationAcknowledgementWizard(models.TransientModel):
    _name = 'registration.acknowledgement.wizard'
    _description = 'Registration Acknowledgement Wizard'

    message = fields.Text(string='Message')
    so_id = fields.Many2one(comodel_name='sale.order', string='Sale Order')
    wiz_for = fields.Selection([
        ('registration', 'Registration Acknowledgement'),
        ('booking', 'Booking Acknowledgement'),
        ('kyc_verification', 'KYC Verification Acknowledgement')
    ], 'Wizard For', default='registration')

    def action_confirm(self):
        if self.wiz_for == 'registration':
            self.so_id.state = 'registered'

        elif self.wiz_for == 'booking':
            self.so_id.state = 'booked'
        
        elif self.wiz_for == 'kyc_verification':
            self.so_id.state = 'in_agreement'