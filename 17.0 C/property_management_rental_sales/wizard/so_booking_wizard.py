from odoo import api, models, fields, _


class SOBookingWizard(models.TransientModel):
    _name = 'so.booking.wizard'
    _description = 'SO Booking Wizard'

    so_id = fields.Many2one('sale.order', required=True)
    partner_id = fields.Many2one('res.partner', related='so_id.partner_id')
    payment_plan_id = fields.Many2one('so.payment.plan', 'Payment Plan', required=True)

    def action_confirm(self):
        Booking = self.env['so.booking'].sudo()
        booking_vals = {
            'so_id': self.so_id.id,
            'partner_id': self.partner_id.id,
            'payment_plan_id': self.payment_plan_id.id,
            'property_id': self.so_id.property_id.id,
            'unit_id': self.so_id.unit_id.id,
            'expiration_date': self.so_id.eoi_expiration,
            'currency_id': self.so_id.currency_id.id,
            'amount': self.so_id.eoi_amount,
            'down_payment_percentage': self.payment_plan_id.down_payment_percentage
        }
        booking = Booking.search([
            ('so_id', '=', self.so_id.id),
        ])
        if not booking:
            booking = Booking.create(booking_vals)
        if booking:
            self.so_id.payment_plan_id = self.payment_plan_id.id
            self.so_id.booking_id = booking.id
            self.so_id.action_confirm()
    