from odoo import fields, models, api, _
from odoo.exceptions import UserError, ValidationError
from dateutil.relativedelta import relativedelta


class PropertyContract(models.Model):
    _name = 'property.contract'
    _description = 'Property Tenancy Contract'
    _inherit = ['portal.mixin', 'mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='Tenancy #', required=True, copy=False, readonly=True, default=lambda self: 'New')
    state = fields.Selection([
        ('draft', 'Draft'),
        ('active', 'Active'),
        ('settled', 'Settled'),
        ('expired', 'Expired'),
        ('terminated', 'Terminated'),
        ('done', 'Done'),
        ('cancel', 'Cancelled'),
        ('non_renew', 'Non Renew'),
        ('renewed', 'Renewed'),
    ], string='Status', default='draft', tracking=True)

    # Contract Information
    start_date = fields.Date(string='Start Date', required=True, tracking=True)
    # Make end_date optional at DB level to avoid NotNullViolation during imports/creates
    end_date = fields.Date(string='End Date', tracking=True)
    duration_id = fields.Many2one('property.duration', string='Duration', required=True)
    duration_days = fields.Integer(string='Duration (Days)', compute='_compute_duration', store=True)
    contract_value = fields.Monetary(string='Rent', required=True, tracking=True)
    rent_per_month = fields.Monetary(string='Rent per Month', store=True, compute='_compute_rent_per_month')
    sale_price = fields.Monetary(string='Sale Price', required=True, tracking=True)
    rent_period = fields.Selection([
        ('monthly', 'Month'),
        ('quarterly', 'Quarter'),
        ('yearly', 'Year')
    ], string='Rent Period', default='monthly')
    payment_term = fields.Selection([
        ('monthly', 'Monthly'),
        ('quarterly', 'Quarterly'),
        ('yearly', 'Yearly')
    ], string='Payment Term', default='quarterly')
    security_deposit = fields.Monetary(string='Security Deposit')
    admin_fee = fields.Monetary('Admin Fee', currency_field='currency_id')
    terminate_date = fields.Date(string='Terminate Date')
    invoice_start_date = fields.Date(string='Invoice Start From')

    # Property Details
    property_id = fields.Many2one('property.property', string='Property', required=True,
                                  domain="[('state', '=', 'available')]")
    unit_id = fields.Many2one('property.unit', string='Unit', ondelete='cascade')
    property_for = fields.Selection([
        ('rent', 'For Rent'),
    ], string="Property For", default='rent')
    property_type_id = fields.Many2one('property.type', related='property_id.property_type_id', string='Property Type')
    street = fields.Char(related='property_id.street', string='Street')
    street2 = fields.Char(related='property_id.street2', string='Street2')
    zip = fields.Char(related='property_id.zip', string='Zip')
    city_id = fields.Many2one(related='property_id.city_id', string='City')
    state_id = fields.Many2one('res.country.state', related='property_id.state_id', string='State')
    country_id = fields.Many2one('res.country', related='property_id.country_id', string='Country')
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company)

    # Parties
    partner_id = fields.Many2one('res.partner', string='Tenant / Customer', required=True,
                                domain="[('partner_type', '=', 'tenant')]", tracking=True)
    tenant_code = fields.Char(string="Tenant Code", tracking=True)
    nationality = fields.Char(string="Nationality", tracking=True)
    profession = fields.Char(string="Profession", tracking=True)
    trade_license_no = fields.Char(string="Trade License No", tracking=True)
    license_expiry_date = fields.Date(string="License Expiry Date", tracking=True)
    visa_type = fields.Selection([
        ('visit', 'Visit Visa'),
        ('tourist', 'Tourist Visa'),
        ('employment', 'Employment Visa'),
        ('student', 'Student Visa'),
        ('residence', 'Residence Visa'),
        ('other', 'Other'),
    ], string="Visa Type", tracking=True)
    visa_expiry_date = fields.Date(string="Visa Expiry Date", tracking=True)
    po_box_number = fields.Char(string="PO Box Number", tracking=True)

    phone = fields.Char(string='Mobile', tracking=True)
    mobile = fields.Char(string='Alternative Mobile', tracking=True)
    email = fields.Char(string='Email', tracking=True)
    landlord_id = fields.Many2one('res.partner', string='Landlord', related='property_id.landlord_id')

    # Broker Details
    is_broker_commission = fields.Boolean(string='Is Broker/Agent Commission?')
    broker_id = fields.Many2one('res.partner', string='Broker', domain="[('partner_type', '=', 'broker')]")
    brokerage_type = fields.Selection([('one_month', 'One Month'), ('all_month', 'All Month')], string='Brokerage Type',
                                      default='one_month')
    commission_type = fields.Selection([('fix', 'Fix'), ('percentage', 'Percentage')], string='Commission Type',
                                       default='fix')
    commission = fields.Monetary(string='Commission')

    # Installment Items
    installment_product_id = fields.Many2one('product.product', string='Installment Item',
                                             domain="[('type', '=', 'service')]")
    broker_product_id = fields.Many2one('product.product', string='Broker Item', domain="[('type', '=', 'service')]")
    deposit_product_id = fields.Many2one('product.product', string='Deposit Item', domain="[('type', '=', 'service')]")

    # Taxes
    is_property_taxes = fields.Boolean(string='Is Taxes?')
    taxes_on_installment = fields.Boolean(string='Taxes on Installment')
    taxes_on_deposit = fields.Boolean(string='Taxes on Deposit')
    tax_ids = fields.Many2many('account.tax', string='Taxes')

    # Agreement
    signed_agreement = fields.Binary(string='Signed Agreement')
    responsible_id = fields.Many2one('res.users', string='Responsible', default=lambda self: self.env.user)

    # Installments
    installment_ids = fields.One2many('property.invoice', 'contract_id', string='Rent Installments')
    maintenance_request_ids = fields.One2many('maintenance.request', 'contract_id', string='Maintenance Requests')
    contract_agreement = fields.Html(string='Contract Agreement')
    terms_and_conditions = fields.Html(string='Terms & Conditions')

    # Calculation
    currency_id = fields.Many2one('res.currency', related='company_id.currency_id')
    untaxed_amount = fields.Monetary(string='Untaxed Amount', compute='_compute_amounts', store=True)
    tax_amount = fields.Monetary(string='Tax Amount', compute='_compute_amounts', store=True)
    total_amount = fields.Monetary(string='Total Amount', compute='_compute_amounts', store=True)
    paid_amount = fields.Monetary(string='Paid Amount', compute='_compute_amounts', store=True)
    remaining_amount = fields.Monetary(string='Remaining Amount', compute='_compute_amounts', store=True)
    invoice_count = fields.Integer(string="Invoice Count", compute='_compute_invoice_count')
    credit_note_count = fields.Integer('Total Credit Notes', compute='_compute_invoice_count')
    bill_count = fields.Integer(string="Bill Count", compute='_compute_bill_count')
    maintenance_request_count = fields.Integer(string="Maintenance Count", compute='_compute_maintenance_request_count')
    settlement_count = fields.Integer(string="Settlement Count", compute='_compute_settlement_count')
    payment_schedule_ids = fields.One2many('property.payment', 'contract_id', string='Payment Schedules')
    lead_id = fields.Many2one('crm.lead', string='Lead')
    payment_count = fields.Integer('Total Payments', compute='_compute_total_payments')
    parent_id = fields.Many2one('property.contract', string='Parent Contract')
    child_id = fields.Many2one('property.contract', string='Child Contract')

    @api.depends('contract_value', 'rent_period')
    def _compute_rent_per_month(self):
        for rec in self:
            monthly_rent = 0
            if rec.rent_period == 'monthly':
                monthly_rent = rec.contract_value
            elif rec.rent_period == 'quarterly':
                monthly_rent = rec.contract_value / 3
            elif rec.rent_period == 'yearly':
                monthly_rent = rec.contract_value / 12
            rec.rent_per_month = monthly_rent

    def action_view_child_contract(self):
        self.ensure_one()
        res_id = False
        if self.child_id:
            res_id = self.child_id.id
        else:
            res_id = self.env['property.contract'].sudo().search([('parent_id', '=', self.id)], limit=1).id
        self.child_id = res_id
        return {
            'name': 'Renewal Contract',
            'type': 'ir.actions.act_window',
            'res_model': 'property.contract',
            'view_mode': 'form',
            'res_id': res_id,
            'target': 'current',
        }

    def action_view_parent_contract(self):
        self.ensure_one()
        if not self.parent_id:
            raise UserError('No parent contract found.')
        return {
            'name': 'Parent Contract',
            'type': 'ir.actions.act_window',
            'res_model': 'property.contract',
            'view_mode': 'form',
            'res_id': self.parent_id.id,
            'target': 'current',
        }

    def action_renew_contract(self):
        self.ensure_one()
        if self.state != 'active':
            raise UserError('Only active contracts can be renewed.')
        
        # Create a copy of the current contract with updated dates and state
        new_contract = self.copy({
            'name': self.env['ir.sequence'].sudo().next_by_code('property.contract') or 'New',
            'start_date': self.end_date + relativedelta(days=1) if self.end_date else fields.Date.today(),
            'end_date': False,  # Will be computed based on duration
            'state': 'draft',
            'parent_id': self.id,
        })

        # Find deposit type line from payment_schedule_ids and reassign to new contract
        deposit_payment = self.payment_schedule_ids.filtered(lambda p: p.type == 'deposit')
        if deposit_payment:
            deposit_payment.write({'contract_id': new_contract.id})

        self.write({
            'state': 'renewed',
            'child_id': new_contract.id,
        })
        
        self.unit_id.write({
            'state': 'available',
        })

        return {
            'name': 'Renew Contract',
            'type': 'ir.actions.act_window',
            'res_model': 'property.contract',
            'view_mode': 'form',
            'res_id': new_contract.id,
            'target': 'current',
        }

    def cron_action_change_state_non_renew(self):
        today = fields.Date.today()
        contracts = self.search([
            ('state', '=', 'active'),
            ('end_date', '<=', today),
        ])
        contracts.write({'state': 'non_renew'})

    def _compute_access_url(self):
        super(PropertyContract, self)._compute_access_url()
        for contract in self:
            contract.access_url = '/my/rent-contracts/%s' % contract.id

    def action_view_payments(self):
        return {
            'name': 'Payments',
            'type': 'ir.actions.act_window',
            'model': 'ir.actions.act_window',
            'res_model': 'account.payment',
            'view_mode': 'tree,form',
            'domain': [
                ('contract_id', '=', self.id)
            ],
            'context': {
                'default_contract_id': self.id
            }
        }

    @api.depends('payment_schedule_ids')
    def _compute_total_payments(self):
        for rec in self:
            rec.payment_count = self.env['account.payment'].search_count([
                ('contract_id', '=', rec.id),
                ('payment_type', '=', 'inbound')
            ])

    @api.onchange('partner_id')
    def _action_get_partner_details(self):
        if self.partner_id:
            self.tenant_code = self.partner_id.tenant_code
            self.nationality = self.partner_id.nationality
            self.profession = self.partner_id.profession
            self.trade_license_no = self.partner_id.trade_license_no
            self.license_expiry_date = self.partner_id.license_expiry_date
            self.visa_type = self.partner_id.visa_type
            self.visa_expiry_date = self.partner_id.visa_expiry_date
            self.po_box_number = self.partner_id.po_box_number
            self.phone = self.partner_id.phone
            self.mobile = self.partner_id.mobile
            self.email = self.partner_id.email
        else:
            # Clear fields if no partner selected
            self.tenant_code = ''
            self.nationality = ''
            self.profession = ''
            self.trade_license_no = ''
            self.license_expiry_date = ''
            self.visa_type = ''
            self.visa_expiry_date = ''
            self.po_box_number = ''
            self.phone = ''
            self.mobile = ''
            self.email = ''

    def _compute_settlement_count(self):
        
        for rec in self:
            rec.settlement_count = self.env['contract.settlement'].search_count([('contract_id', '=', rec.id)])

    def _compute_maintenance_request_count(self):
        for rec in self:
            rec.maintenance_request_count = self.env['maintenance.request'].search_count([('contract_id', '=', rec.id)])

    def action_view_sale_orders(self):
        self.ensure_one()
        return {
            'name': 'Sale Orders',
            'type': 'ir.actions.act_window',
            'res_model': 'sale.order',
            'view_mode': 'tree,form',
            'domain': [('contract_id', '=', self.id)],
            'context': {'default_contract_id': self.id}
        }

    def _compute_invoice_count(self):
        for rec in self:
            rec.invoice_count = self.env['account.move'].search_count([
                ('contract_id', '=', rec.id),
                ('move_type', '=', 'out_invoice')
            ])
            rec.credit_note_count = self.env['account.move'].search_count([
                ('contract_id', '=', rec.id),
                ('move_type', '=', 'out_refund')
            ])

    def action_view_credit_notes(self):
        self.ensure_one()
        return {
            'name': 'Credit Notes',
            'type': 'ir.actions.act_window',
            'res_model': 'account.move',
            'view_mode': 'tree,form',
            'domain': [
                ('contract_id', '=', self.id),
                ('move_type', '=', 'out_refund')
            ],
            'context': {
                'default_contract_id': self.id,
                'search_default_draft': 1
            }
        }

    def _compute_bill_count(self):
        for rec in self:
            rec.bill_count = self.env['account.move'].search_count([('contract_id', '=', rec.id), ('move_type', '=', 'in_invoice')])


    def action_view_invoices(self):
        self.ensure_one()
        return {
            'name': 'Invoices',
            'type': 'ir.actions.act_window',
            'res_model': 'account.move',
            'view_mode': 'tree,form',
            'domain': [
                ('contract_id', '=', self.id),
                ('move_type', '=', 'out_invoice')
            ],
            'context': {
                'default_contract_id': self.id,
                'default_move_type': 'out_invoice',
                'default_partner_id': self.partner_id.id,
                'default_property_id': self.property_id.id,
                'default_property_unit_id': self.unit_id.id,
                'search_default_draft': 1
            }
        }

    def action_view_bills(self):
        self.ensure_one()
        return {
            'name': 'Bills',
            'type': 'ir.actions.act_window',
            'res_model': 'account.move',
            'view_mode': 'tree,form',
            'domain': [('contract_id', '=', self.id), ('move_type', '=', 'in_invoice')],
            'context': {'default_contract_id': self.id}
        }

    def action_view_maintenance_requests(self):
        self.ensure_one()
        return {
            'name': 'Maintenance Requests',
            'type': 'ir.actions.act_window',
            'res_model': 'maintenance.request',
            'view_mode': 'tree,form',
            'domain': [('contract_id', '=', self.id)],
            'context': {
                'default_contract_id': self.id,
                'default_unit_id': self.unit_id.id,
                'default_partner_id': self.partner_id.id,
            }
        }

    def action_view_settlements(self):
        self.ensure_one()
        action =  {
            'name': 'Settlements',
            'type': 'ir.actions.act_window',
            'res_model': 'contract.settlement',
            'view_mode': 'tree,form',
            'domain': [('contract_id', '=', self.id)],
            'context': {'default_contract_id': self.id}
        }
        if self.settlement_count == 1:
            settlement = self.env['contract.settlement'].sudo().search([
                ('contract_id', '=', self.id)
            ], limit=1)
            action.update({
                'res_id': settlement.id,
                'view_mode': 'form'
            })
        return action

    @api.depends('start_date', 'duration_id.duration', 'duration_id.duration_unit')
    def _compute_duration(self):
        """Compute end_date from start_date + duration and compute a human friendly duration_days string.

        Behavior:
        - If both start_date and duration_id are set, end_date is computed from start_date + duration (using unit).
        - duration_days is stored as a string like '90 Day(s)'.
        - If inputs are missing, both fields are cleared.
        """
        for rec in self:
            # Clear defaults
            rec.duration_days = 0
            # Only compute when we have enough data
            if not (rec.start_date and rec.duration_id and rec.duration_id.duration):
                rec.end_date = False
                continue

            dur = int(rec.duration_id.duration)
            unit = rec.duration_id.duration_unit or 'months'
            if unit == 'days':
                delta = relativedelta(days=dur)
            elif unit == 'weeks':
                delta = relativedelta(days=dur * 7)
            elif unit == 'months':
                delta = relativedelta(months=dur)
            elif unit == 'years':
                delta = relativedelta(years=dur)
            else:
                delta = relativedelta(months=dur)

            # Compute end_date and duration in days (approx for months/years using relativedelta difference)
            try:
                rec.end_date = rec.start_date + delta - relativedelta(days=1)  # inclusive of start date
                # compute exact day difference between start and computed end
                # start_date and end_date are date objects; subtraction yields a timedelta
                days = (rec.end_date - rec.start_date).days
                rec.duration_days = days + 1  # inclusive of both start and end dates
            except Exception:
                rec.end_date = False
                rec.duration_days = 0

    @api.depends('installment_ids.amount', 'installment_ids.vat', 'installment_ids.price_total', 'installment_ids.payment_status')
    def _compute_amounts(self):
        for rec in self:
            untaxed = sum(rec.installment_ids.mapped('amount'))
            tax = sum(rec.installment_ids.mapped('vat'))
            total = sum(rec.installment_ids.mapped('price_total'))
            paid = sum(rec.installment_ids.filtered(lambda i: i.payment_status == 'paid').mapped('price_total'))
            
            rec.untaxed_amount = untaxed
            rec.tax_amount = tax
            rec.total_amount = total
            rec.paid_amount = paid
            rec.remaining_amount = total - paid

    def _actual_end_date(self):
        dur = int(self.duration_id.duration)
        unit = self.duration_id.duration_unit or 'months'
        if unit == 'days':
            delta = relativedelta(days=dur)
        elif unit == 'weeks':
            delta = relativedelta(days=dur * 7)
        elif unit == 'months':
            delta = relativedelta(months=dur)
        elif unit == 'years':
            delta = relativedelta(years=dur)
        else:
            delta = relativedelta(months=dur)

        if self.invoice_start_date:
            actual_end_date = self.invoice_start_date + delta
        else:
            actual_end_date = self.start_date + delta
        return actual_end_date

    def action_generate_installments(self):
        for contract in self:
            if any([line.invoice_id for line in contract.installment_ids]):
                raise UserError(_("You can't generate installments when invoice is available!"))

            if any([line.payment_id for line in contract.payment_schedule_ids]):
                raise UserError(_("You can't generate installments when payment is available!"))

            if contract.state != 'draft':
                raise UserError('You can only generate installments for contracts in the "Draft" state.')

            # Clear existing installments
            contract.installment_ids.unlink()

            payments_to_create = []
            # Create Security Deposit
            if contract.security_deposit > 0:
                print('security: ', contract.security_deposit)
                journal = self.env['account.journal'].sudo().search([
                    ('type', 'in', ('bank', 'cash'))
                ], limit=1, order="id asc")
                payment_method = self.env['account.payment.method.line'].sudo().search([
                    ('payment_type', '=', 'inbound'),
                    ('journal_id', '=', journal.id if journal else False)
                ], limit=1, order='id asc')

                deposit_payment_line = self.env['property.payment'].sudo().search([
                    ('type', '=', 'deposit'),
                    ('contract_id', '=', contract.id),
                ], limit=1)
                if not deposit_payment_line:
                    # Calculate deposit amount with taxes if applicable
                    deposit_amount = contract.security_deposit
                    if contract.taxes_on_deposit and contract.tax_ids:
                        base_line = self.env['account.tax']._prepare_base_line_for_taxes_computation(
                            contract,
                            tax_ids=contract.tax_ids,
                            price_unit=contract.security_deposit,
                            quantity=1.0,
                            partner_id=contract.partner_id,
                            currency_id=contract.currency_id or self.env.company.currency_id,
                        )
                        self.env['account.tax']._add_tax_details_in_base_line(base_line, contract.company_id)
                        deposit_amount = base_line['tax_details']['raw_total_included_currency']
                    print('deposit amount: ', deposit_amount)
                    
                    payments_to_create.append({
                        'due_date': contract.start_date,
                        'journal_id': journal.id,
                        'payment_method_id': payment_method.id,
                        'amount': deposit_amount,
                        'type': 'deposit',
                        'contract_id': contract.id,
                    })

            print('payemnt to create: ', payments_to_create)
            if payments_to_create:
                self.env['property.payment'].sudo().create(payments_to_create)

            installments_to_create = []
            # Create admin fee installments
            if contract.admin_fee > 0:
                installments_to_create.append({
                    'invoice_date': contract.start_date,
                    'amount': contract.admin_fee,
                    'invoice_type': 'fees',
                    'description': f"Admin Fee",
                    'contract_id': contract.id,
                })

            # Determine monthly rent
            monthly_rent = 0
            if contract.rent_period == 'monthly':
                monthly_rent = contract.contract_value
            elif contract.rent_period == 'quarterly':
                monthly_rent = contract.contract_value / 3
            elif contract.rent_period == 'yearly':
                monthly_rent = contract.contract_value / 12

            if monthly_rent <= 0:
                continue  # Skip if no contract_value is set

            # Determine installment amount and period
            installment_amount = 0
            period_delta = None
            if contract.payment_term == 'monthly':
                installment_amount = monthly_rent
                period_delta = relativedelta(months=1)
            elif contract.payment_term == 'quarterly':
                installment_amount = monthly_rent * 3
                period_delta = relativedelta(months=3)
            elif contract.payment_term == 'yearly':
                installment_amount = monthly_rent * 12
                period_delta = relativedelta(years=1)

            if not period_delta:
                continue

            # Generate installments
            next_date = contract.invoice_start_date or contract.start_date
            actual_end_date = self._actual_end_date()
            if not actual_end_date:
                raise ValidationError('You can only generate installments for with contract end date.')
            while next_date <= actual_end_date:
                installments_to_create.append({
                    'invoice_date': next_date,
                    'amount': installment_amount,
                    'invoice_type': 'rent',
                    'description': f"Rent for {next_date.strftime('%B %Y')}",
                    'contract_id': contract.id,
                })
                next_date += period_delta

            if installments_to_create:
                self.env['property.invoice'].create(installments_to_create[:-1])
        return True

    def action_set_draft(self):
        for contract in self:
            contract.state = 'draft'
            contract.unit_id.state = 'available'

    def action_activate_contract(self):
        for contract in self:
            if contract.state != 'draft':
                raise UserError('Only draft contracts can be activated.')

            if contract.unit_id.state not in ['available', 'reserved']:
                raise UserError('The selected unit is not available or reserved.')

            # Generate installments if they don't exist
            if not contract.installment_ids:
                contract.action_generate_installments()

            if not contract.installment_ids and contract.property_for != 'sale':
                raise UserError('Cannot activate a contract with no installment lines. Please generate them first.')

            # Assign sequence number on activation if not set (or still the default 'New')
            if not contract.name or contract.name == 'New':
                seq = self.env['ir.sequence'].sudo().next_by_code('property.contract')
                contract.name = seq or contract.name or 'New'

            contract.state = 'active'

            # Set Unit to Rented or Leased
            contract.unit_id.state = 'rented'

    def action_expire_contract(self):
        for contract in self:
            if contract.state != 'active':
                raise UserError('Only active contracts can be expired.')
            contract.state = 'expired'

    def action_terminate_contract(self):
        for contract in self:
            if contract.state != 'active':
                raise UserError('Only active contracts can be terminated.')
            self.terminate_date = fields.Date.today()
            contract.state = 'terminated'

    def action_create_invoice(self):
        self.ensure_one()
        return {
            'name': 'Create Invoice',
            'type': 'ir.actions.act_window',
            'res_model': 'property.invoice.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_contract_id': self.id,
                'default_property_id': self.property_id.id,
                'default_property_unit_id': self.unit_id.id,
                'default_partner_id': self.partner_id.id,
                'default_invoice_date': fields.Date.today(),
            }
        }

    def action_create_bill(self):
        self.ensure_one()
        return {
            'name': 'Create Bills',
            'type': 'ir.actions.act_window',
            'res_model': 'property.bill.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_contract_id': self.id,
                'default_partner_id': self.partner_id.id,
                'default_invoice_date': fields.Date.today(),
            }
        }

    def action_create_sale_order(self):
        self.ensure_one()
        if not self.installment_product_id:
            raise UserError('Please set an Installment Item for the Sales contract.')

        price = self.sale_price

        order_line = [(0, 0, {
            'product_id': self.installment_product_id.id,
            'name': self.installment_product_id.name,
            'product_uom_qty': 1,
            'price_unit': price,
        })]

        sale_order_vals = {
            'partner_id': self.partner_id.id,
            'order_line': order_line,
            'state': 'draft',
        }

        sale_order = self.env['sale.order'].create(sale_order_vals)
        self.unit_id.write({'state': 'sold'})

        return {
            'name': 'Sale Order',
            'type': 'ir.actions.act_window',
            'res_model': 'sale.order',
            'view_mode': 'form',
            'res_id': sale_order.id,
            'target': 'current',
        }


    def action_contract_settlement(self):
        self.ensure_one()
        return {
            'name': 'Contract Settlement',
            'type': 'ir.actions.act_window',
            'res_model': 'contract.settlement',
            'view_mode': 'form',
            'target': 'current',
            'context': {
                'default_contract_id': self.id,
                'default_partner_id': self.partner_id.id,
                'default_property_id': self.property_id.id,
                'default_unit_id': self.unit_id.id,
            }
        }
