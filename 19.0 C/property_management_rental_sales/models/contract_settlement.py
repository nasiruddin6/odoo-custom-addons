from odoo import fields, models, api
from odoo.exceptions import UserError
import math

class ContractSettlement(models.Model):
    _name = 'contract.settlement'
    _description = 'Contract Settlement'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'settlement_date desc, id desc'

    # Basic Information
    name = fields.Char(string='Settlement Reference', required=True, copy=False, readonly=True,
                       default=lambda self: 'New', tracking=True)
    settlement_date = fields.Date(string='Settlement Date', required=True, tracking=True)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirmed', 'Confirmed'),
        ('done', 'Done'),
        ('settled', 'Settled'),
        ('cancelled', 'Cancelled')
    ], string='Status', default='draft', tracking=True)

    # Contract Reference
    contract_id = fields.Many2one('property.contract', string='Contract', required=True,
                                  ondelete='restrict', tracking=True)

    # Settlement Type & Reason
    settlement_type = fields.Selection([
        ('early_termination', 'Early Termination'),
        ('normal_end', 'Normal Contract End'),
        ('breach', 'Contract Breach'),
        ('mutual_agreement', 'Mutual Agreement')
    ], string='Settlement Type', required=True, tracking=True)
    termination_reason = fields.Text(string='Termination Reason', tracking=True)

    # Date Tracking
    actual_end_date = fields.Date(string='Actual End Date', required=True,
                                  help="Actual date when tenant vacated the property", tracking=True)
    notice_date = fields.Date(string='Notice Date', help="Date when settlement notice was given", tracking=True)
    contract_start_date = fields.Date(related='contract_id.start_date', string='Contract Start Date', store=True)
    contract_end_date = fields.Date(related='contract_id.end_date', string='Contract End Date', store=True)

    # Financial Breakdown
    total_rent = fields.Monetary(string='Total Contract Rent', required=True, currency_field='currency_id',
                                 tracking=True)
    occupied_rent = fields.Monetary(string='Occupied Period Rent', required=True, currency_field='currency_id',
                                    help="Rent for actual occupied period", tracking=True)
    security_deposit = fields.Monetary(string='Security Deposit', currency_field='currency_id', tracking=True)
    refund_amount = fields.Monetary(string='Refund', currency_field='currency_id', tracking=True)
    unpaid_rent = fields.Monetary(string='Unpaid Rent', currency_field='currency_id', tracking=True)
    penalty_charges = fields.Monetary(string='Penalty Charges', currency_field='currency_id', help="Penalty for early termination", tracking=True)
    fees = fields.Monetary(string='Fees', currency_field='currency_id', help="Fees", tracking=True)
    maintenance_charges = fields.Monetary(string='Maintenance/Repair Charges', currency_field='currency_id',
                                          help="Deductions for damages/repairs", tracking=True)
    utility_charges = fields.Monetary(string='Utility Charges', currency_field='currency_id',
                                      help="Outstanding utility bills", tracking=True)
    other_charges = fields.Monetary(string='Other Charges', currency_field='currency_id', tracking=True)
    other_charges_description = fields.Text(string='Other Charges Description')

    # Payment Details
    payment_method = fields.Selection([
        ('cash', 'Cash'),
        ('bank_transfer', 'Bank Transfer'),
        ('cheque', 'Cheque'),
        ('credit_note', 'Credit Note')
    ], string='Payment Method', tracking=True)
    payment_reference = fields.Char(string='Payment Reference', help="Transaction/Cheque reference number",
                                    tracking=True)
    payment_date = fields.Date(string='Payment Date', tracking=True)
    bank_account_id = fields.Many2one('res.partner.bank', string='Bank Account',
                                      help="Bank account for refund transfer")

    # Related Records
    invoice_ids = fields.Many2many('account.move', 'settlement_invoice_rel', 'settlement_id', 'invoice_id',
                                   string='Related Invoices', domain="[('move_type', '=', 'out_invoice')]")
    paid_invoice_count = fields.Integer(string='Paid Invoices', compute='_compute_invoice_counts', store=True)
    unpaid_invoice_count = fields.Integer(string='Unpaid Invoices', compute='_compute_invoice_counts', store=True)
    credit_note_count = fields.Integer('Total Credit Notes', compute='_compute_invoice_counts', store=True)
    credit_note_id = fields.Many2one('account.move', string='Credit Note',
                                     domain="[('move_type', '=', 'out_refund')]",
                                     help="Credit note for deposit refund")
    invoice_id = fields.Many2one('account.move', string='Invoice',
                                     domain="[('move_type', '=', 'out_refund')]",
                                     help="Invoice for tenant payable")

    # Property Condition
    property_condition = fields.Selection([
        ('excellent', 'Excellent'),
        ('good', 'Good'),
        ('fair', 'Fair'),
        ('poor', 'Poor'),
        ('damaged', 'Damaged')
    ], string='Property Condition', help="Condition of property at handover", tracking=True)
    inspection_date = fields.Date(string='Inspection Date', tracking=True)
    inspection_notes = fields.Text(string='Inspection Notes')
    damage_description = fields.Text(string='Damage Description')

    # Parties Involved
    partner_id = fields.Many2one(related='contract_id.partner_id', string='Tenant', store=True)
    landlord_id = fields.Many2one(related='contract_id.landlord_id', string='Landlord', store=True)
    property_id = fields.Many2one(related='contract_id.property_id', string='Property', store=True)
    unit_id = fields.Many2one(related='contract_id.unit_id', string='Unit', store=True)

    # Documentation
    settlement_agreement = fields.Binary(string='Signed Settlement Agreement', attachment=True)
    settlement_agreement_filename = fields.Char(string='Agreement Filename')
    inspection_report = fields.Binary(string='Property Inspection Report', attachment=True)
    inspection_report_filename = fields.Char(string='Inspection Report Filename')
    handover_certificate = fields.Binary(string='Property Handover Certificate', attachment=True)
    handover_certificate_filename = fields.Char(string='Handover Certificate Filename')
    tenant_acknowledgement = fields.Binary(string='Tenant Acknowledgement', attachment=True)
    tenant_acknowledgement_filename = fields.Char(string='Acknowledgement Filename')

    # Accounting Integration
    journal_id = fields.Many2one('account.journal', string='Journal',
                                 domain="[('type', 'in', ['general', 'bank', 'cash'])]")
    move_id = fields.Many2one('account.move', string='Journal Entry', readonly=True,
                              help="Accounting entry for settlement")
    reconciled = fields.Boolean(string='Reconciled', default=False, tracking=True,
                                help="Whether all accounts are reconciled")

    # Workflow & Approval
    approved_by = fields.Many2one('res.users', string='Approved By', readonly=True, tracking=True)
    approval_date = fields.Datetime(string='Approval Date', readonly=True)
    responsible_user_id = fields.Many2one('res.users', string='Responsible',
                                          default=lambda self: self.env.user, tracking=True)

    # Computed Summary
    net_payable = fields.Monetary(string='Net Payable', compute='_compute_totals',
                                  store=True, currency_field='currency_id',
                                  help="Final net amount payable to tenant or landlord")
    amount = fields.Monetary(string='Settlement Amount', compute='_compute_totals',
                             store=True, currency_field='currency_id', tracking=True)
    settlement_summary = fields.Html(string='Settlement Summary', compute='_compute_settlement_summary')

    # Rental Period Calculation
    days_occupied = fields.Integer(string='Days Occupied', compute='_compute_rental_period', store=True)
    rent_per_day = fields.Monetary(string='Rent Per Day', compute='_compute_rental_period',
                                   store=True, digits=(16, 6))
    remaining_days = fields.Integer(string='Remaining Days', compute='_compute_rental_period',
                                    store=True, help="Days remaining in contract (for early termination)")

    # Currency & Company
    currency_id = fields.Many2one(related='contract_id.currency_id', string='Currency', store=True)
    company_id = fields.Many2one(related='contract_id.company_id', string='Company', store=True)
    total_paid = fields.Monetary('Total Paid (Without Deposit)', currency_field='currency_id') #Total paid without deposit amount
    total_receivable = fields.Monetary('Total Receivable', currency_field='currency_id', compute="_compute_totals")
    total_paid_to_show = fields.Monetary('Total Paid', currency_field='currency_id', compute="_compute_totals") # total Paid with deposit amount

    # ==================== Compute Methods ====================

    @api.depends('contract_id.start_date', 'actual_end_date', 'contract_end_date')
    def _compute_rental_period(self):
        """Calculate days occupied, rent per day, and remaining days"""
        for record in self:
            if record.contract_id and record.contract_id.start_date and record.actual_end_date:
                start = record.contract_id.start_date
                actual_end = record.actual_end_date
                contract_end = record.contract_end_date

                # Calculate days occupied
                delta = actual_end - start
                record.days_occupied = delta.days + 1  # +1 to include both start and end date

                # Calculate rent per day
                if record.days_occupied > 0:
                    # Calculate total contract days
                    if contract_end and start:
                        contract_value = record.contract_id.contract_value
                        rent_per_day = 0
                        rent_period = record.contract_id.rent_period
                        if rent_period == 'monthly':
                            rent_per_day = round(contract_value * 12 / 365, 6)
                        elif rent_period == 'quarterly':
                            rent_per_day = round(contract_value * 4 / 365, 6)
                        elif rent_period == 'yearly':
                            rent_per_day = round(contract_value / 365, 6)
                        record.rent_per_day = rent_per_day
                    else:
                        record.rent_per_day = 0
                else:
                    record.rent_per_day = 0

                # Calculate remaining days (for early termination)
                if contract_end and actual_end < contract_end:
                    remaining_delta = contract_end - actual_end
                    record.remaining_days = remaining_delta.days
                else:
                    record.remaining_days = 0
            else:
                record.days_occupied = 0
                record.rent_per_day = 0
                record.remaining_days = 0

    @api.depends('maintenance_charges', 'utility_charges',
                 'other_charges', 'penalty_charges', 'fees', 'security_deposit',
                 'occupied_rent', 'unpaid_rent', 'total_paid')
    def _compute_totals(self):
        """Calculate total deductions, net payable, and settlement amount"""
        for record in self:
            charges = record.maintenance_charges + record.utility_charges + record.penalty_charges + record.fees + record.other_charges
            net = record.total_paid + record.security_deposit - record.occupied_rent - charges - record.refund_amount
            record.total_receivable = record.occupied_rent + charges
            record.total_paid_to_show = record.total_paid + record.security_deposit
            record.net_payable = net
            record.amount = abs(net)

    @api.depends('invoice_ids', 'invoice_ids.payment_state')
    def _compute_invoice_counts(self):
        """Count paid and unpaid invoices"""
        for record in self:
            paid_count = 0
            unpaid_count = 0
            for invoice in record.invoice_ids:
                if invoice.payment_state in ['paid', 'in_payment']:
                    paid_count += 1
                else:
                    unpaid_count += 1
            record.paid_invoice_count = paid_count
            record.unpaid_invoice_count = unpaid_count
            record.credit_note_count = self.env['account.move'].search_count([
                ('contract_id', '=', record.contract_id.id),
                ('move_type', '=', 'out_refund')
            ])

    @api.depends('security_deposit', 'net_payable',
                 'occupied_rent', 'unpaid_rent', 'penalty_charges', 'fees', 'settlement_type', 'refund_amount')
    def _compute_settlement_summary(self):
        """Generate HTML summary of settlement calculation"""
        for record in self:
            if not record.contract_id:
                record.settlement_summary = '<p>No contract selected</p>'
                continue

            # Conditionally add refund row
            refund_row = ""
            if record.refund_amount:
                refund_row = f"""
                        <tr>
                            <td style="padding: 8px; border: 1px solid #dee2e6; padding-left: 20px;">Less: Refunds</td>
                            <td style="padding: 8px; border: 1px solid #dee2e6; text-align: right;">-{record.currency_id.symbol}{record.refund_amount:,.2f}</td>
                        </tr>"""

            summary = f"""
            <div style="font-family: Arial, sans-serif; padding: 10px;">
                <h3 style="color: #2c3e50;">Settlement Summary</h3>
                <table style="width: 100%; border-collapse: collapse;">
                    <tr style="background-color: #f8f9fa;">
                        <td style="padding: 8px; border: 1px solid #dee2e6;"><strong>Contract:</strong></td>
                        <td style="padding: 8px; border: 1px solid #dee2e6;">{record.contract_id.name}</td>
                    </tr>
                    <tr>
                        <td style="padding: 8px; border: 1px solid #dee2e6;"><strong>Settlement Type:</strong></td>
                        <td style="padding: 8px; border: 1px solid #dee2e6;">{dict(record._fields['settlement_type'].selection).get(record.settlement_type, '')}</td>
                    </tr>
                    <tr style="background-color: #f8f9fa;">
                        <td style="padding: 8px; border: 1px solid #dee2e6;"><strong>Days Occupied:</strong></td>
                        <td style="padding: 8px; border: 1px solid #dee2e6;">{record.days_occupied} days</td>
                    </tr>
                </table>
                
                <h4 style="color: #2c3e50; margin-top: 20px;">Financial Breakdown</h4>
                <table style="width: 100%; border-collapse: collapse;">
                    <tr style="background-color: #e8f5e9;">
                        <td style="padding: 8px; border: 1px solid #dee2e6; padding-left: 20px;"><strong>Total Contract Rent:</strong></td>
                        <td style="padding: 8px; border: 1px solid #dee2e6; text-align: right;">{record.currency_id.symbol}{record.total_rent:,.2f}</td>
                    </tr>
                    <tr style="background-color: #e8f5e9;">
                        <td style="padding: 8px; border: 1px solid #dee2e6; padding-left: 20px;"><strong>Unpaid Rent:</strong></td>
                        <td style="padding: 8px; border: 1px solid #dee2e6; text-align: right;">{record.currency_id.symbol}{record.unpaid_rent:,.2f}</td>
                    </tr>
                    <tr style="background-color: #e8f5e9;">
                        <td style="padding: 8px; border: 1px solid #dee2e6; padding-left: 20px;"><strong>Total Receivable:</strong></td>
                        <td style="padding: 8px; border: 1px solid #dee2e6; text-align: right;">{record.currency_id.symbol}{record.total_receivable:,.2f}</td>
                    </tr>
                    <tr>
                        <td style="padding: 8px; border: 1px solid #dee2e6; padding-left: 20px;">Add: Total Paid</td>
                        <td style="padding: 8px; border: 1px solid #dee2e6; text-align: right;">+{record.currency_id.symbol}{record.total_paid_to_show:,.2f}</td>
                    </tr>
                    <tr>
                        <td style="padding: 8px; border: 1px solid #dee2e6; padding-left: 20px;">Less: Occupied Rent</td>
                        <td style="padding: 8px; border: 1px solid #dee2e6; text-align: right;">-{record.currency_id.symbol}{record.occupied_rent:,.2f}</td>
                    </tr>
                    <tr>
                        <td style="padding: 8px; border: 1px solid #dee2e6; padding-left: 20px;">Less: Maintenance/Repair Charges</td>
                        <td style="padding: 8px; border: 1px solid #dee2e6; text-align: right;">-{record.currency_id.symbol}{record.maintenance_charges:,.2f}</td>
                    </tr>
                    <tr>
                        <td style="padding: 8px; border: 1px solid #dee2e6; padding-left: 20px;">Less: Utility Charges</td>
                        <td style="padding: 8px; border: 1px solid #dee2e6; text-align: right;">-{record.currency_id.symbol}{record.utility_charges:,.2f}</td>
                    </tr>
                    <tr>
                        <td style="padding: 8px; border: 1px solid #dee2e6; padding-left: 20px;">Less: Penalty Charges</td>
                        <td style="padding: 8px; border: 1px solid #dee2e6; text-align: right;">-{record.currency_id.symbol}{record.penalty_charges:,.2f}</td>
                    </tr>
                    <tr>
                        <td style="padding: 8px; border: 1px solid #dee2e6; padding-left: 20px;">Less: Fees</td>
                        <td style="padding: 8px; border: 1px solid #dee2e6; text-align: right;">-{record.currency_id.symbol}{record.fees:,.2f}</td>
                    </tr>
                    <tr>
                        <td style="padding: 8px; border: 1px solid #dee2e6; padding-left: 20px;">Less: Other Charges</td>
                        <td style="padding: 8px; border: 1px solid #dee2e6; text-align: right;">-{record.currency_id.symbol}{record.other_charges:,.2f}</td>
                    </tr>{refund_row}
                    <tr style="background-color: #{'#ffebee' if record.net_payable < 0 else '#e8f5e9'}; font-weight: bold;">
                        <td style="padding: 8px; border: 1px solid #dee2e6;"><strong>Net {'Payable to Tenant' if record.net_payable >= 0 else 'Due from Tenant'}:</strong></td>
                        <td style="padding: 8px; border: 1px solid #dee2e6; text-align: right;">{record.currency_id.symbol}{abs(record.net_payable):,.2f}</td>
                    </tr>
                </table>
            </div>
            """
            record.settlement_summary = summary

    # ==================== CRUD Methods ====================

    @api.model_create_multi
    def create(self, vals_list):
        """Generate sequence for settlement reference and validate data"""
        for vals in vals_list:
            if vals.get('name', 'New') == 'New':
                vals['name'] = self.env['ir.sequence'].next_by_code('contract.settlement') or 'New'

        records = super(ContractSettlement, self).create(vals_list)

        for record in records:
            # Auto-populate security deposit from contract
            if record.contract_id and not record.security_deposit:
                deposit_payment = sum(self.contract_id.payment_schedule_ids.filtered(lambda
                                                                                         payment: payment.type == 'deposit' and payment.payment_id != False and payment.payment_status in [
                    'in_process', 'paid']).mapped('payment_id.amount_company_currency_signed'))

                record.security_deposit = deposit_payment or 0.00

        return records

    def write(self, vals):
        """Override write to add validation"""
        return super(ContractSettlement, self).write(vals)

    # ==================== Onchange Methods ====================

    @api.onchange('contract_id', 'actual_end_date')
    def _onchange_contract_id(self):
        """Auto-populate fields when contract is selected"""
        if self.contract_id:
            self.total_rent =  sum(self.contract_id.installment_ids.filtered(lambda x: x.invoice_type in ['rent', 'lease']).mapped('amount'))
            deposit_refund_payments = self.env['account.payment'].sudo().search([
                ('payment_type', '=', 'outbound'),
                ('contract_id', '=', self.contract_id.id),
                ('partner_id', '=', self.partner_id.id),
                ('state', 'in', ['in_process', 'paid'])
            ])
            deposit_refund = sum(deposit_refund_payments.mapped('amount'))
            self.refund_amount = deposit_refund
            deposit_payment = sum(self.contract_id.payment_schedule_ids.filtered(lambda payment: payment.type == 'deposit' and payment.payment_id != False and payment.payment_status in ['in_process', 'paid']).mapped('payment_id.amount_company_currency_signed'))
            self.security_deposit = deposit_payment or 0.00

            # Payments
            payments = self.env['account.payment'].sudo().search([
                ('contract_id', '=', self.contract_id.id),
                ('payment_type', '=', 'inbound'),
                ('state', 'in', ['in_process', 'paid'])
            ])
            total_payment = sum(payments.mapped('amount'))
            self.total_paid = total_payment - deposit_payment

            # Get unpaid rent from invoices
            unpaid_rent_invoices = self.env['property.invoice'].search(
                [('invoice_type', '=', 'rent'), ('contract_id', '=', self.contract_id.id)])
            total_rent_residual = sum(
                unpaid_rent_invoices.mapped('invoice_id.amount_residual')
            )
            self.unpaid_rent = (total_rent_residual)

            # Populate invoice_ids
            all_invoices = self.env['account.move'].search([
                ('contract_id', '=', self.contract_id.id),
                ('move_type', '=', 'out_invoice')
            ])
            self.invoice_ids = [(6, 0, all_invoices.ids)]

            occupied_rent = self.days_occupied * self.rent_per_day
            self.occupied_rent = math.ceil(occupied_rent) if self.contract_id.duration_days == self.days_occupied else occupied_rent

            # changes and deduction defaults
            change_invoices = self.env['property.invoice'].search([
                ('invoice_type', '!=', 'rent'),
                ('contract_id', '=', self.contract_id.id)
            ])
            maintenance_invoices = change_invoices.filtered(lambda inv: inv.invoice_type == 'maintenance')
            total_maintenance_residual = sum(maintenance_invoices.mapped('invoice_id.amount_total'))
            self.maintenance_charges = total_maintenance_residual

            utility_invoices = change_invoices.filtered(lambda inv: inv.invoice_type == 'utility')
            total_utility_residual = sum(utility_invoices.mapped('invoice_id.amount_total'))
            self.utility_charges = total_utility_residual

            other_invoices = change_invoices.filtered(lambda inv: inv.invoice_type == 'other')
            total_other_residual = sum(other_invoices.mapped('invoice_id.amount_total'))
            self.other_charges = total_other_residual

            penalty_invoices = change_invoices.filtered(lambda inv: inv.invoice_type == 'penalty')
            total_penalty_residual = sum(penalty_invoices.mapped('invoice_id.amount_total'))
            self.penalty_charges = total_penalty_residual

            penalty_invoices_fees = change_invoices.filtered(lambda inv: inv.invoice_type == 'fees')
            total_fees_residual = sum(penalty_invoices_fees.mapped('invoice_id.amount_total'))
            self.fees = total_fees_residual

            other_invoices = change_invoices.filtered(lambda inv: inv.invoice_type == 'other')
            total_other_residual = sum(other_invoices.mapped('invoice_id.amount_total'))
            self.other_charges = total_other_residual

            print(total_maintenance_residual + total_utility_residual + total_other_residual)

    # ==================== Action Methods ====================

    def action_confirm(self):
        """Confirm the settlement"""
        for record in self:
            if record.state != 'draft':
                raise UserError("Only draft settlements can be confirmed.")

            # Validations
            if not record.actual_end_date:
                raise UserError("Please set the actual end date.")

            if not record.settlement_type:
                raise UserError("Please select a settlement type.")

            record.state = 'confirmed'
            record.message_post(body=f"Settlement confirmed by {self.env.user.name}")

    def action_done(self):
        """Mark settlement as done and update related records"""
        for record in self:
            if record.state != 'confirmed':
                raise UserError("Only confirmed settlements can be marked as done.")

            # Validate payment details if refund is due
            if record.net_payable > 0 and not record.payment_method:
                raise UserError("Please specify the payment method for the refund.")

            # Update contract state
            if record.contract_id:
                if record.settlement_type == 'early_termination':
                    record.contract_id.state = 'terminated'
                else:
                    record.contract_id.state = 'done'

                # Update property/unit availability
                if record.unit_id:
                    record.unit_id.state = 'available'
                    record.unit_id.partner_id = False

                if record.property_id:
                    record.property_id.state = 'available'

            record.state = 'done'
            record.approved_by = self.env.user
            record.approval_date = fields.Datetime.now()
            record.message_post(body=f"Settlement completed by {self.env.user.name}")

    def action_cancel(self):
        """Cancel the settlement"""
        for record in self:
            if record.state == 'done':
                raise UserError("Done settlements cannot be cancelled. Please create a reversal instead.")
            record.state = 'cancelled'
            record.message_post(body=f"Settlement cancelled by {self.env.user.name}")

    def action_reset_to_draft(self):
        """Reset settlement to draft state"""
        for record in self:
            if record.state not in ['confirmed', 'cancelled']:
                raise UserError("Only confirmed or cancelled settlements can be reset to draft.")
            record.state = 'draft'
            record.message_post(body=f"Settlement reset to draft by {self.env.user.name}")

    # ==================== Smart Button Actions ====================

    def action_view_contract(self):
        """Open the related contract"""
        self.ensure_one()
        return {
            'name': 'Contract',
            'type': 'ir.actions.act_window',
            'res_model': 'property.contract',
            'view_mode': 'form',
            'res_id': self.contract_id.id,
            'target': 'current',
        }

    def action_view_invoices(self):
        """View all related invoices"""
        self.ensure_one()
        invoice_ids = self.invoice_ids.filtered(lambda inv: inv.payment_state in ['paid', 'in_payment']).ids
        return {
            'name': 'Related Invoices',
            'type': 'ir.actions.act_window',
            'res_model': 'account.move',
            'view_mode': 'list,form',
            'domain': [('id', 'in', invoice_ids)],
            'context': {'default_contract_id': self.contract_id.id}
        }
    
    def action_view_unpaid_invoices(self):
        """View all related invoices"""
        self.ensure_one()
        invoice_ids = self.invoice_ids.filtered(lambda inv: inv.payment_state not in ['paid', 'in_payment']).ids
        return {
            'name': 'Related Invoices',
            'type': 'ir.actions.act_window',
            'res_model': 'account.move',
            'view_mode': 'list,form',
            'domain': [('id', 'in', invoice_ids)],
            'context': {'default_contract_id': self.contract_id.id}
        }
    
    def action_view_credit_notes(self):
        self.ensure_one()
        return {
            'name': 'Credit Notes',
            'type': 'ir.actions.act_window',
            'res_model': 'account.move',
            'view_mode': 'list,form',
            'domain': [
                ('contract_id', '=', self.contract_id.id),
                ('move_type', '=', 'out_refund')
            ],
            'context': {
                'default_contract_id': self.contract_id.id,
                'search_default_draft': 1
            }
        }
    
    def action_create_journal_entry(self):
        """Create accounting journal entry for settlement"""
        self.ensure_one()

        if self.move_id:
            raise UserError("A journal entry already exists for this settlement.")

        if not self.journal_id:
            raise UserError("Please select a journal first.")

        # This is a placeholder - implement based on your accounting requirements
        raise UserError("Journal entry creation needs to be configured based on your chart of accounts.")

    def action_print_settlement(self):
        """Print settlement report"""
        self.ensure_one()
        return self.env.ref('property_management_rental_sales.action_report_contract_settlement').report_action(self)

    def action_recompute_settlement(self):
        self._compute_totals()
        self._compute_rental_period()
        self._onchange_contract_id()

    def action_launch_settlement_wizard(self):
        # # If Net payable is negative than create invoice to take payment from tenant
        # self.action_recompute_settlement()
        action = {
            'name': 'Contract Settlement Acknowledgement',
            'type': 'ir.actions.act_window',
            'model': 'ir.actions.act_window',
            'res_model': 'contract.settlement.wizard',
            'target': 'new',
            'view_mode': 'form',
            'context': {
                'default_partner_id': self.partner_id.id,
                'default_property_id': self.property_id.id,
                'default_unit_id': self.unit_id.id,
                'default_contract_id': self.contract_id.id,
                'default_currency_id': self.currency_id.id,
                'default_settlement_id': self.id,
                'default_type': 'equal',
                'default_amount': abs(self.net_payable),
            }
        }
        if self.net_payable < 0:
            # Create invoice and take payment
            action['context'].update({
                'default_type': 'receive',
            })
        if self.net_payable > 0:
            action['context'].update({
                'default_type': 'send',
            })
        return action