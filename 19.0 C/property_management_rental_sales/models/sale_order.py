from odoo import fields, models, api, _
from odoo.exceptions import UserError, ValidationError
import math
from dateutil.relativedelta import relativedelta



class SaleOrder(models.Model):
    _inherit = 'sale.order'

    property_id = fields.Many2one('property.property', string='Property', store=True)
    unit_id = fields.Many2one('property.unit', string='Unit', store=True)
    installment_ids = fields.One2many('so.installment.line', 'so_id', string='Installment Plans')
    state = fields.Selection(selection_add=[
        ('draft', 'Draft'),
        ('offer_received', 'Offer Received'),
        ('negotiation', 'Negotiation'),
        ('under_review', 'Under Review'),
        ('offer_accepted', 'Offer Accepted'),
        ('booked', 'Booked'),
        ('waiting_for_kyc', 'Waiting For KYC Verification'),
        ('in_agreement', 'In Agreement'),
        ('spa_signed', 'SPA Signed'),
        ('due_diligence', 'Due Diligence'),
        ('in_payment', 'In Payment'),
        ('waiting_registration', 'Waiting for Registration'),
        ('registered', 'Registered'),
        ('sold', 'sold')
    ])

    is_spa = fields.Boolean(
        string='SPA Order',
        help='Enable if this order represents a SPA (Sale & Purchase Agreement).'
    )
    booking_id = fields.Many2one('so.booking', 'Booking')

    #=======================================================================================================
    # EOI Payment
    #=======================================================================================================
    eoi_amount = fields.Monetary('EOI Amount', currency_field='currency_id', compute='_compute_eoi_paid_amount')
    eoi_paid = fields.Monetary('EOI Paid', currency_field='currency_id', compute='_compute_eoi_paid_amount')
    eoi_expiration = fields.Date('EOI Expiration Date')
    eoi_payment_id = fields.Many2one(
        'account.payment',
        string='EOI Payments'
    )

    #========================================================================================================================
    # Breakdown
    #========================================================================================================================
    payment_plan_id = fields.Many2one('so.payment.plan', 'Payment Plan')
    unit_price_amount = fields.Monetary(string="Unit Price", currency_field='currency_id', compute='_compute_unit_price_amount', store=True)
    down_payment_amount = fields.Monetary('Down Payment', currency_field='currency_id', compute='_compute_down_breakdown', store=True)
    pre_handover_amount = fields.Monetary('Pre-Handover Payment', currency_field='currency_id', compute='_compute_down_breakdown', store=True)
    on_handover_amount = fields.Monetary('On-Handover Payment', currency_field='currency_id', compute='_compute_down_breakdown', store=True)
    post_handover_amount = fields.Monetary('Post-Handover Payment', currency_field='currency_id', compute='_compute_down_breakdown', store=True)
    amount_per_installment = fields.Monetary('Amount Per Installment', currency_field='currency_id', compute='_compute_down_breakdown', store=True)
    pre_handover_installment_count = fields.Integer('Pre-Handover Installments', compute='_compute_down_breakdown', store=True)
    post_handover_installment_count = fields.Integer('Post-Handover Installments', compute='_compute_down_breakdown', store=True)

    # Additional Fees
    admin_fee = fields.Monetary(string="Admin Fee", currency_field='currency_id', related='booking_id.admin_fee')
    stamp_duty_fee = fields.Monetary(string="Stamp Duty Fee", currency_field='currency_id', related='booking_id.stamp_duty_fee')
    registration_fee = fields.Monetary(string="Registration Fee", currency_field='currency_id', related='booking_id.registration_fee')
    mutation_fee = fields.Monetary(string="Mutation Fee", currency_field='currency_id', related='booking_id.mutation_fee')
    others_fee = fields.Monetary(string="Others Fees", currency_field='currency_id', related='booking_id.others_fee')
    total_fees = fields.Monetary(
        string="Total Fees",
        currency_field='currency_id',
        related='booking_id.total_fees',
        store=True
    )
    is_hide_installment_btn = fields.Boolean('Hide Generate Installment', compute='_compute_btns')
    is_hide_down_payment_btn = fields.Boolean('Hide Down Payment Button', compute='_compute_btns')
    is_hide_payment_btn = fields.Boolean('Hide Payment Button', compute='_compute_btns')
    is_hide_register_btn = fields.Boolean('Hide Register Button', compute='_compute_btns')
    payment_line_ids = fields.One2many('property.payment', 'so_id', string='Payment Lines')
    payment_count = fields.Integer(string='Payment Count', compute='_compute_payment_inv_count')
    spa_invoice_count = fields.Integer(string='Invoice Count', compute='_compute_payment_inv_count')

    def _compute_payment_inv_count(self):
        for rec in self:
            rec.payment_count = self.env['account.payment'].search_count([('so_id', '=', rec.id)])
            rec.spa_invoice_count = self.env['account.move'].search_count([('so_id', '=', rec.id)])

    @api.model_create_multi
    def create(self, vals):
        res = super(SaleOrder, self).create(vals)
        if res.is_spa:
            res.name = self.env['ir.sequence'].next_by_code('property.sales.order')
        return res

    @api.depends('installment_ids')
    def _compute_btns(self):
        
        for rec in self:
            down_payment = False
            installment = False
            payment = True
            register = True

            down_payment_line = rec.installment_ids.filtered(lambda x: x.type == 'down_payment')
            if (down_payment_line and down_payment_line.payment_state in ['in_payment', 'paid']) or rec.state != 'in_agreement' or not rec.installment_ids:
                down_payment = True
                if down_payment_line.payment_state in ['in_payment', 'paid'] and rec.state == 'in_agreement':
                    payment = False

            if any(line.invoice_id for line in rec.installment_ids) or rec.state != 'in_agreement':
                installment = True

            if all(line.invoice_id and line.payment_state in ['in_payment', 'paid'] for line in rec.installment_ids) and rec.state == 'in_payment':
                register = False

            rec.is_hide_down_payment_btn = down_payment
            rec.is_hide_installment_btn = installment
            rec.is_hide_payment_btn = payment
            rec.is_hide_register_btn = register

    def action_view_booking(self):
        self.ensure_one()
        return {
            'name': 'Booking',
            'type': 'ir.actions.act_window',
            'model': 'ir.actions.act_window',
            'res_model': 'so.booking',
            'view_mode': 'form',
            'target': 'current',
            'res_id': self.booking_id.id
        }

    @api.depends('eoi_payment_id')
    def _compute_eoi_paid_amount(self):
        for rec in self:
            rec.eoi_paid = 0
            rec.eoi_amount = rec.eoi_payment_id.amount if rec.eoi_payment_id else 0
            if rec.eoi_payment_id and rec.eoi_payment_id.state in ['paid', 'in_process']:
                rec.eoi_paid = rec.eoi_payment_id.amount

    def action_pay_eoi(self):
        self.ensure_one()

        if self.eoi_payment_id:
            raise ValidationError(_('EOI is already paid!'))

        return {
            'name': 'EOI Payment',
            'type': 'ir.actions.act_window',
            'model': 'ir.actions.act_window',
            'res_model': 'eoi.payment.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_so_id': self.id,
                'default_eoi_amount': self.eoi_amount
            }
        }

    def action_generate_invoice(self):
        self.ensure_one()
        return {
            'name': 'Generate Invoice',
            'type': 'ir.actions.act_window',
            'model': 'ir.actions.act_window',
            'res_model': 'so.invoice.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_so_id': self.id,
                'default_partner_id': self.partner_id.id,
                'default_partner_id': self.partner_id.id,
            }
        }

    def action_create_down_payment(self):
        self.ensure_one()
        down_payment_line = self.installment_ids.filtered(lambda x: x.type == 'down_payment')
        if not down_payment_line:
            self.action_so_generate_installments()
            down_payment_line = self.installment_ids.filtered(lambda x: x.type == 'down_payment')

        invoice_id = down_payment_line.invoice_id
        if not invoice_id:
            down_payment_line.action_create_invoice()
            invoice_id = down_payment_line.invoice_id

        return {
            'name': 'Down Payment',
            'type': 'ir.actions.act_window',
            'model': 'ir.actions.act_window',
            'res_model': 'eoi.payment.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_so_id': self.id,
                'default_amount': down_payment_line.amount,
                'default_wiz_for': 'down_payment',
                'reconcile_invoice_id': invoice_id.id
            }
        }

    def action_so_generate_installments(self):
        self.ensure_one()
        if self.installment_ids:
            if any(line.invoice_id for line in self.installment_ids):
                raise ValidationError(
                    _('Running installments cannot be re-generated. Some installments already have invoices.'))

            self.installment_ids.unlink()

        create_vals = []
        inv_date = fields.Date.today()
        gap = self.payment_plan_id.collection_gaps

        if self.down_payment_amount:
            create_vals.append({
                'name': 'Down Payment',
                'type': 'down_payment',
                'invoice_date': inv_date,
                'amount': self.down_payment_amount,
            })

        if self.admin_fee:
            create_vals.append({
                'name': 'Admin Fees',
                'type': 'admin_fees',
                'invoice_date': inv_date,
                'amount': self.admin_fee,
            })

        if self.stamp_duty_fee:
            create_vals.append({
                'name': 'Stamp Duty Fee',
                'type': 'stamp_duty',
                'invoice_date': inv_date,
                'amount': self.stamp_duty_fee,
            })

        if self.registration_fee:
            create_vals.append({
                'name': 'Registration Fees',
                'type': 'registration',
                'invoice_date': inv_date,
                'amount': self.registration_fee,
            })

        if self.mutation_fee:
            create_vals.append({
                'name': 'Mutation Fee',
                'type': 'mutation',
                'invoice_date': inv_date,
                'amount': self.mutation_fee,
            })

        if self.others_fee:
            create_vals.append({
                'name': 'Others Fees',
                'type': 'others',
                'invoice_date': inv_date,
                'amount': self.others_fee,
            })

        if self.pre_handover_installment_count and self.pre_handover_installment_count > 0:

            i = 1
            while i <= int(self.pre_handover_installment_count):
                inv_date += relativedelta(months=gap)

                create_vals.append({
                    'name': f'Pre-Handover Installment {i}',
                    'type': 'installment_before',
                    'invoice_date': inv_date,
                    'amount': self.amount_per_installment,
                })

                i += 1
        # Installment on handover
        if self.on_handover_amount:
            inv_date += relativedelta(months=gap)
            create_vals.append({
                'name': 'On Handover Installment',
                'type': 'installment_on',
                'invoice_date': inv_date,
                'amount': self.on_handover_amount,
            })

        # Post handover installments
        if self.post_handover_installment_count and self.post_handover_installment_count > 0:
            i = 1
            total = 0
            while i <= int(self.post_handover_installment_count):
                inv_date += relativedelta(months=gap)

                if i != self.post_handover_installment_count:
                    total += self.amount_per_installment
                    create_vals.append({
                        'name': f'Post-Handover Installment {i}',
                        'type': 'installment_after',
                        'invoice_date': inv_date,
                        'amount': self.amount_per_installment,
                    })
                else:
                    create_vals.append({
                        'name': f'Post-Handover Installment {i}',
                        'type': 'installment_after',
                        'invoice_date': inv_date,
                        'amount': self.post_handover_amount - total,
                    })

                i+=1
        self.installment_ids = [(0, 0, vals) for vals in create_vals]

    def action_send_for_payment(self):
        self.ensure_one()
        if not self.signature:
            raise UserError('Contract Signature not found')
        self.state = 'in_payment'

    def action_send_for_register(self):
        self.ensure_one()
        if any(line.payment_state not in ['in_payment', 'paid'] for line in self.installment_ids):
            raise UserError(_('Please Pay all installment first!'))
        self.state = 'waiting_registration'

    def action_confirm_registration(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Acknowledgement'),
            'res_model': 'registration.acknowledgement.wizard',
            'model': 'ir.actions.act_window',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_message': 'Property Registration Acknowledgement \nWe confirm that the property registration is complete..',
                'default_so_id': self.id,
                'default_wiz_for': 'registration'
            }
        }

    def action_sale(self):
        self.state = 'sold'

    @api.depends('unit_price_amount', 'payment_plan_id')
    def _compute_down_breakdown(self):
        for rec in self:
            down_payment_amount = 0
            pre_handover_amount = 0
            on_handover_amount = 0
            post_handover_amount = 0
            amount_per_installment = 0
            pre_handover_installments = 0
            post_handover_installments = 0
            if rec.payment_plan_id:
                plan = rec.payment_plan_id
                down_payment_amount = ((rec.unit_price_amount * plan.down_payment_percentage) / 100) or 0
                pre_handover_amount = ((rec.unit_price_amount * plan.pre_handover_percentage) / 100) or 0
                on_handover_amount = ((rec.unit_price_amount * plan.on_handover_percentage) / 100) or 0
                post_handover_amount = rec.unit_price_amount - down_payment_amount - pre_handover_amount - on_handover_amount or 0

                # Fix: Check if duration is non-zero before division
                if plan.duration:
                    amount_per_installment = ((pre_handover_amount + post_handover_amount) * plan.collection_gaps) / plan.duration
                else:
                    amount_per_installment = 0

                # Fix: Check if amount_per_installment is non-zero before division
                if amount_per_installment:
                    pre_handover_installments = math.ceil(pre_handover_amount / amount_per_installment)
                    post_handover_installments = math.ceil(post_handover_amount / amount_per_installment)
                else:
                    pre_handover_installments = 0
                    post_handover_installments = 0

            rec.down_payment_amount = down_payment_amount
            rec.pre_handover_amount = pre_handover_amount
            rec.on_handover_amount = on_handover_amount
            rec.post_handover_amount = post_handover_amount
            rec.amount_per_installment = amount_per_installment
            rec.pre_handover_installment_count = pre_handover_installments
            rec.post_handover_installment_count = post_handover_installments

    @api.depends('unit_id')
    def _compute_unit_price_amount(self):
        for rec in self:
            rec.unit_price_amount = rec.amount_total

    def action_recompute(self):
        self._compute_unit_price_amount()
        self._compute_down_breakdown()

    def action_create_invoice(self):
        res = super().create_invoice()

        return res

    def action_view_payments(self):
        self.ensure_one()
        payments = self.env['account.payment'].search([('so_id', '=', self.id)])
        
        if len(payments) == 1:
            return {
                'name': 'Payment',
                'type': 'ir.actions.act_window',
                'model': 'ir.actions.act_window',
                'res_model': 'account.payment',
                'view_mode': 'form',
                'target': 'current',
                'res_id': payments.id
            }
        else:
            return {
                'name': 'Payments',
                'type': 'ir.actions.act_window',
                'model': 'ir.actions.act_window',
                'res_model': 'account.payment',
                'view_mode': 'list,form',
                'target': 'current',
                'domain': [('id', 'in', payments.ids)],
                'context': {
                    'default_so_id': self.id,
                    'default_partner_id': self.partner_id.id,
                    'search_default_state_draft': 1,
                    'default_property_id': self.property_id.id,
                    'default_property_unit_id': self.unit_id.id,
                }
            }
        
    def action_view_invoices(self):
        self.ensure_one()
        invoices = self.env['account.move'].search([('so_id', '=', self.id)])
        
        if len(invoices) == 1:
            return {
                'name': 'Invoice',
                'type': 'ir.actions.act_window',
                'model': 'ir.actions.act_window',
                'res_model': 'account.move',
                'view_mode': 'form',
                'target': 'current',
                'res_id': invoices.id
            }
        else:
            return {
                'name': 'Invoices',
                'type': 'ir.actions.act_window',
                'model': 'ir.actions.act_window',
                'res_model': 'account.move',
                'view_mode': 'list,form',
                'target': 'current',
                'domain': [('id', 'in', invoices.ids)],
                'context': {
                    'default_so_id': self.id,
                    'default_partner_id': self.partner_id.id,
                    'search_default_draft': 1,
                    'default_property_id': self.property_id.id,
                    'default_property_unit_id': self.unit_id.id,
                }
            }
            

    def action_confirm_booking(self):
        self.ensure_one()
        if self.eoi_amount and (not self.eoi_payment_id or self.eoi_amount != self.eoi_paid):
            raise ValidationError(_("Please Pay EOI amount first!"))
        
        if not self.booking_id:
            raise ValidationError(_("Please Create Booking first!"))
        
        if not self.booking_id or self.booking_id.state != 'confirmed' or self.booking_id.payment_state not in ['paid', 'in_process']:
            raise ValidationError(_("Booking must be confirmed before confirming the contract!"))

        return {
            'type': 'ir.actions.act_window',
            'name': _('Acknowledgement'),
            'res_model': 'registration.acknowledgement.wizard',
            'model': 'ir.actions.act_window',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_message': 'The contract has been successfully booked.',
                'default_so_id': self.id,
                'default_wiz_for': 'booking'
            }
        }
    
    def action_create_booking(self):
        self.ensure_one()
        vals = {
            'name': f'Booking for {self.name}',
            'so_id': self.id,
            'expiration_date': self.eoi_expiration or fields.Date.today() + relativedelta(months=1),
            'payment_plan_id': self.payment_plan_id.id,
        }
        
        booking = self.env['so.booking'].search([('so_id', '=', self.id)], limit=1)
        if not booking:
            booking = self.env['so.booking'].create(vals)
        self.booking_id = booking.id

        return {
            'name': 'Booking',
            'type': 'ir.actions.act_window',
            'model': 'ir.actions.act_window',
            'res_model': 'so.booking',
            'res_id': booking.id,
            'view_mode': 'form',
            'target': 'current',
        }

    def action_send_for_kyc_verification(self):
        self.ensure_one()
        if self.state != 'booked':
            raise ValidationError(_("Please Book the Contract first!"))
        self.state = 'waiting_for_kyc'

    def action_confirm_kyc_verification(self):
        self.ensure_one()
        if self.partner_id.kyc_status != 'verified':
            return {
                'name': 'KYC Verification',
                'type': 'ir.actions.act_window',
                'model': 'ir.actions.act_window',
                'res_model': 'res.partner',
                'view_mode': 'form',
                'res_id': self.partner_id.id,
                'target': 'current',
            }

        else:
            return {
            'type': 'ir.actions.act_window',
            'name': _('Acknowledgement'),
            'res_model': 'registration.acknowledgement.wizard',
            'model': 'ir.actions.act_window',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_message': 'KYC Already Acknowledged \nThe KYC verification for this user has already been completed and acknowledged. No further action is required.',
                'default_so_id': self.id,
                'default_wiz_for': 'kyc_verification'
            }
        }

    def _prepare_confirmation_values(self):
        """ Prepare the sales order confirmation values.

        Note: self can contain multiple records.

        :return: Sales Order confirmation values
        :rtype: dict
        """
        if self.is_spa:
            return {
                'state': 'booked',
                'date_order': fields.Datetime.now()
            }
        return {
            'state': 'sale',
            'date_order': fields.Datetime.now()
        }
