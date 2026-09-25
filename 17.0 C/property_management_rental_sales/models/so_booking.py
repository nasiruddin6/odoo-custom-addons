from odoo import api, models, fields, _
from odoo.exceptions import UserError


class SOBooking(models.Model):
    _name = 'so.booking'
    _description = 'SO Booking'
    _rec_name = 'name'

    so_id = fields.Many2one('sale.order', 'Contract')
    name = fields.Char('Name')
    partner_id = fields.Many2one('res.partner', 'Customer', related='so_id.partner_id', required=True)
    expiration_date = fields.Date('Expiration Date', required=True)
    currency_id = fields.Many2one('res.currency', 'Currency', related='so_id.currency_id')

    amount = fields.Monetary('Booking Amount', currency_field='currency_id')
    price = fields.Monetary('Price', currency_field='currency_id', required=True, related='so_id.unit_price_amount', readonly=False)
    other_fees = fields.Monetary('Other Fees', currency_field='currency_id')
    payment_plan_id = fields.Many2one('so.payment.plan', 'Payment Plan', required=True)
    down_payment_percentage = fields.Float('Down Payment(%)')
    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirmed', 'Confirmed'),
        ('cancelled', 'Cancelled')
    ], 'Status', default='draft')
    payment_id = fields.Many2one('account.payment', 'Payment')
    payment_state = fields.Selection(related='payment_id.state', string='Payment Status')
    admin_fee = fields.Monetary(string="Admin Fee", currency_field='currency_id')
    stamp_duty_fee = fields.Monetary(string="Stamp Duty Fee", currency_field='currency_id')
    registration_fee = fields.Monetary(string="Registration Fee", currency_field='currency_id')
    mutation_fee = fields.Monetary(string="Mutation Fee", currency_field='currency_id')
    others_fee = fields.Monetary(string="Others Fees", currency_field='currency_id')
    total_fees = fields.Monetary(
        string="Total Fees",
        currency_field='currency_id',
        compute='_compute_total_fees',
        store=True
    )

    #=======================================================================================================
    # Property Informations
    #=======================================================================================================
    property_id = fields.Many2one('property.property', 'Property', related='so_id.property_id')
    unit_id = fields.Many2one('property.unit', 'Unit', related='so_id.unit_id')
    floor = fields.Char('Floor / Level', related='unit_id.floor')
    building = fields.Char(string='Building / Block', related='unit_id.building')
    area_sqft = fields.Float(string='Area (sqft)', related='unit_id.area_sqft')
    property_unit_type_id = fields.Many2one('property.unit.type', string='Unit Type', help='Type of the unit based on number of bedrooms', related='unit_id.property_unit_type_id')
    bedroom = fields.Integer(string='Bedrooms', related='unit_id.bedroom')
    living = fields.Integer(string='Living', related='unit_id.living')
    dining = fields.Integer(string='Dining', related='unit_id.dining')
    kitchen = fields.Integer(string='Kitchen', related='unit_id.kitchen')
    bathroom = fields.Integer(string='Bathrooms', related='unit_id.bathroom')
    balcony = fields.Integer(string='Balconies', related='unit_id.balcony')
    parking = fields.Integer(string='Parking Spaces', related='unit_id.parking')
    facing = fields.Selection(related='unit_id.facing', string='Facing Direction')
    furnishing_type = fields.Selection(related='unit_id.furnishing_type', string='Furnishing Type')

    @api.depends('admin_fee', 'stamp_duty_fee', 'registration_fee', 'mutation_fee', 'others_fee')
    def _compute_total_fees(self):
        for record in self:
            record.total_fees = sum([
                record.admin_fee or 0,
                record.stamp_duty_fee or 0,
                record.registration_fee or 0,
                record.mutation_fee or 0,
                record.others_fee or 0
            ])

    #=======================================================================================================
    # Property Details
    #=======================================================================================================

    @api.model_create_multi
    def create(self, vals):
        res = super().create(vals)
        seq = self.env['ir.sequence'].sudo().next_by_code('so.booking')
        res.name = seq
        return res

    #=======================================================================================================
    # Action Methods
    #=======================================================================================================

    def action_confirm(self):
        """Confirm the booking"""
        self.state = 'confirmed'

    def action_cancel(self):
        """Cancel the booking"""
        if self.so_id and self.so_id.state not in ['draft']:
            raise UserError("Cannot cancel booking because the contract is already confirmed.")

        if self.payment_id:
            self.payment_id.action_cancel()
        self.state = 'cancelled'

    def action_reset_to_draft(self):
        """Reset booking to draft status"""
        self.state = 'draft'

    def action_create_payment(self):
        """Register payment for the booking"""
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'so.booking.payment.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_booking_id': self.id,
            }
        }

    def action_view_payment(self):
        """Open the related payment form for this booking"""
        self.ensure_one()
        if not self.payment_id:
            return False
        return {
            'type': 'ir.actions.act_window',
            'name': _('Payment'),
            'res_model': 'account.payment',
            'view_mode': 'form',
            'res_id': self.payment_id.id,
            'target': 'current',
        }
        