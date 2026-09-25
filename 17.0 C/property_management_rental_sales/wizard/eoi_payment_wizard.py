from odoo import api, models, fields, _

class EOIPaymentWizard(models.TransientModel):
    _name = 'eoi.payment.wizard'
    _description = 'EOI Payment Wizard'

    so_id = fields.Many2one('sale.order', string='Sale Order')
    wiz_for = fields.Selection([
        ('eoi', 'EOI'),
        ('down_payment', 'Down Payment'),
    ], string='Wizard For', default='eoi')
    partner_id = fields.Many2one('res.partner', string='Customer', related='so_id.partner_id')
    currency_id = fields.Many2one('res.currency', string='Currency ID', related='so_id.currency_id')
    eoi_amount = fields.Monetary(string='EOI Amount', currency_field='currency_id')
    amount = fields.Monetary(string='Amount', currency_field='currency_id')
    eoi_expiration = fields.Date('EOI Expiration', required=True, related='so_id.eoi_expiration', readonly=False)
    journal_id = fields.Many2one('account.journal', string='Journal', domain="[('type', 'in', ('bank', 'cash'))]", required=True)
    payment_method_id = fields.Many2one('account.payment.method.line', 'Payment Method', domain="[('payment_type', '=', 'inbound'), ('journal_id', '=', journal_id)]")
    partner_bank_id = fields.Many2one('res.partner.bank', string='Bank')
    cheque_number = fields.Char(string='Cheque Number')
    property_id = fields.Many2one('property.property', string='Property', related='so_id.property_id')
    unit_id = fields.Many2one('property.unit', string='Unit', related='so_id.unit_id')
    date = fields.Date('Payment Date', default=fields.Date.today())

    def action_create_payment(self):
        vals = {
            'payment_type': 'inbound',
            'partner_id': self.partner_id.id,
            'currency_id': self.currency_id.id,
            'date': self.date,
            'journal_id': self.journal_id.id,
            'property_id': self.property_id.id,
            'property_unit_id': self.unit_id.id,
            'payment_method_line_id': self.payment_method_id.id,
            'partner_bank_id': self.partner_bank_id.id,
            'so_id': self.so_id.id,
            'is_eoi_payment': True,
        }
        payment = self.env['account.payment'].sudo().create(vals)
        if self.wiz_for == 'eoi' and payment:
            payment.amount = self.eoi_amount
            self.so_id.write({
                'eoi_payment_id': payment.id,
                'eoi_amount': self.eoi_amount
            })
            return {
                'type': 'ir.actions.act_window',
                'name': _('Payment'),
                'res_model': 'account.payment',
                'view_mode': 'form',
                'res_id': payment.id,
                'target': 'current',
            }

        else:
            payment.amount = self.amount
            inv_id = self.env.context.get('reconcile_invoice_id', '')
            invoice = False
            if inv_id:
                invoice = self.env['account.move'].browse(int(inv_id))
            self._reconcile_inv_payment(payment, invoice)

    def _reconcile_inv_payment(self, payment, invoice):
        """
        Reconciles a single invoice with a single payment.
        """
        if payment and invoice:
            if payment.state != 'posted':
                payment.action_post()
            if invoice.state != 'posted':
                invoice.action_post()

            # Get unreconciled receivable lines from the invoice
            invoice_lines = invoice.line_ids.filtered(
                lambda l: l.account_id.account_type == 'asset_receivable' and not l.reconciled
            )

            # Get unreconciled receivable lines from the payment
            payment_lines = payment.move_id.line_ids.filtered(
                lambda l: l.account_id.account_type == 'asset_receivable' and not l.reconciled
            )

            # Reconcile if both have lines
            if invoice_lines and payment_lines:
                (invoice_lines + payment_lines).reconcile()