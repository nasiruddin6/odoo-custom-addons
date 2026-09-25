from odoo import api, models, fields, _
from odoo.exceptions import ValidationError


class ContractSettlementWizard(models.TransientModel):
    _name = 'contract.settlement.wizard'
    _description = 'Pay'

    company_id = fields.Many2one('res.company', 'Company')
    currency_id = fields.Many2one('res.currency', 'Currency', required=True)
    type = fields.Selection([
        ('receive', 'Receive Money'),
        ('send', 'Send Money'),
        ('equal', 'Equal')
    ], 'Type', required=True)
    journal_id = fields.Many2one('account.journal', 'Journal', domain=[('type', 'in', ['bank', 'cash'])])
    amount = fields.Monetary('Amount', currency_field='currency_id')
    date = fields.Date('Payment Date')
    payment_method_id = fields.Many2one('account.payment.method.line', 'Payment Method', domain="[('payment_type', '=', 'inbound'), ('journal_id', '=', journal_id)]")
    partner_bank_id = fields.Many2one('res.bank', string='Recipient Bank')
    partner_id = fields.Many2one('res.partner', 'Tenant', domain=[('partner_type', '=', 'tenant')])
    property_id = fields.Many2one('property.property', 'Property')
    unit_id = fields.Many2one('property.unit', 'Unit')
    contract_id = fields.Many2one('property.contract', 'Contract')
    settlement_id = fields.Many2one('contract.settlement', 'Settlement')

    @api.model
    def default_get(self, vals):
        res = super().default_get(vals)
        res.update({
            'company_id': self.env.company.id,
            'date': fields.Date.today()
        })
        return res

    def action_settlement(self):
        self.ensure_one()

        # Get all related deposit payments (unreconciled security deposits)
        security_deposit_payments = self.contract_id.payment_schedule_ids.filtered(
            lambda payment: payment.type == 'deposit'
                            and payment.payment_id != False
                            and payment.payment_status in ['in_process', 'paid']
        ).mapped('payment_id')

        if self.type == 'receive':
            # ============================
            # RECEIVE MONEY SCENARIOS (1-3)
            # ============================
            # Just create payment and reconcile with existing unpaid invoices

            # Get all unpaid/partially paid invoices
            unpaid_invoices = self.env['account.move'].sudo().search([
                ('contract_id', '=', self.contract_id.id),
                ('move_type', '=', 'out_invoice'),
                ('payment_state', 'in', ['not_paid', 'partial']),
                ('state', '=', 'posted'),
            ])

            # Create settlement payment for the amount
            settlement_payment = self._action_create_payment(payment_type='inbound')
            settlement_payment.action_post()

            # Combine all payments (security deposits + new settlement payment)
            all_payments = security_deposit_payments | settlement_payment

            # Reconcile existing unpaid invoices with all payments
            self._reconcile_multiple_invoices(unpaid_invoices, all_payments)

        elif self.type == 'send':
            # ============================
            # SEND MONEY SCENARIOS (4-5)
            # ============================

            if not security_deposit_payments:
                raise ValidationError(_("No security deposit payment found to refund."))

            # Check if there are unpaid invoices to offset
            unpaid_invoices = self.env['account.move'].sudo().search([
                ('contract_id', '=', self.contract_id.id),
                ('move_type', '=', 'out_invoice'),
                ('payment_state', 'in', ['not_paid', 'partial']),
                ('state', '=', 'posted'),
            ])

            # Create credit note for the refund amount
            credit_note = self._action_create_credit_note()
            credit_note.action_post()

            # If there are unpaid invoices (Scenario 5 - returned products)
            # Reconcile them first with the deposit
            if unpaid_invoices:
                # Reconcile unpaid invoices with security deposit
                self._reconcile_multiple_invoices(unpaid_invoices, security_deposit_payments)

            # Create outbound payment for the refund
            refund_payment = self._action_create_payment(payment_type='outbound')
            refund_payment.action_post()

            # Reconcile credit note with refund payment (and any remaining deposit)
            remaining_payments = security_deposit_payments | refund_payment
            self._reconcile_multiple_invoices(credit_note, remaining_payments)

        self.settlement_id.action_recompute_settlement()
        self.settlement_id.state = 'settled'

    def _action_create_invoice(self):
        tax_ids = []
        is_sell_invoice = False

        if self.contract_id.property_for == 'rent':
            tax_ids = [(6, 0, self.contract_id.tax_ids.ids)] if self.contract_id.taxes_on_installment else []

        invoice_lines = [(0, 0, {
            'product_id': False,
            'name': f'Contract Settlement for {self.contract_id.name}',
            'quantity': 1,
            'price_unit': self.amount,
            'tax_ids': tax_ids,
        })]

        invoice_vals = {
            'partner_id': self.partner_id.id,
            'is_sell_invoice': is_sell_invoice,
            'move_type': 'out_invoice',
            'invoice_date': self.date or fields.Date.today(),
            'invoice_line_ids': invoice_lines,
            'contract_id': self.contract_id.id or False,
            'property_id': self.property_id.id or False,
            'property_unit_id': self.unit_id.id or False,
            'is_rent_invoice': True,
        }

        return self.env['account.move'].create(invoice_vals)

    def _action_create_credit_note(self):
        tax_ids = []

        if self.contract_id.property_for == 'rent':
            tax_ids = [(6, 0, self.contract_id.tax_ids.ids)] if self.contract_id.taxes_on_installment else []

        credit_note_lines = [(0, 0, {
            'product_id': False,
            'name': f'Security Deposit Refund for {self.contract_id.name}',
            'quantity': 1,
            'price_unit': self.amount,
            'tax_ids': tax_ids,
        })]

        credit_note_vals = {
            'partner_id': self.partner_id.id,
            'move_type': 'out_refund',
            'invoice_date': self.date or fields.Date.today(),
            'invoice_line_ids': credit_note_lines,
            'contract_id': self.contract_id.id or False,
            'property_id': self.property_id.id or False,
            'property_unit_id': self.unit_id.id or False,
            'is_rent_invoice': True,
        }

        return self.env['account.move'].create(credit_note_vals)

    def _action_create_payment(self, payment_type='inbound'):
        vals = {
            'payment_type': payment_type,  # inbound / outbound
            'is_rent_payment': True,
            'partner_id': self.partner_id.id,
            'amount': self.amount,
            'currency_id': self.currency_id.id,
            'date': self.date,
            'journal_id': self.journal_id.id,
            'payment_method_line_id': self.payment_method_id.id,
            'partner_bank_id': self.partner_bank_id.id,
            'property_id': self.property_id.id,
            'property_unit_id': self.unit_id.id,
            'contract_id': self.contract_id.id,
        }
        return self.env['account.payment'].sudo().create(vals)

    def _reconcile_multiple_invoices(self, invoices, payments):
        """
        Reconciles multiple invoices with multiple payments.
        Handles both regular invoices and credit notes.
        """
        # Collect all unreconciled receivable lines from invoices/credit notes
        invoice_lines = invoices.line_ids.filtered(
            lambda l: l.account_id.account_type == 'asset_receivable' and not l.reconciled
        )

        # Collect all unreconciled receivable lines from all payments
        payment_lines = self.env['account.move.line']
        for pay in payments:
            payment_lines |= pay.move_id.line_ids.filtered(
                lambda l: l.account_id.account_type == 'asset_receivable' and not l.reconciled
            )

        # Reconcile everything together
        if invoice_lines and payment_lines:
            (invoice_lines + payment_lines).reconcile()