from odoo import models, fields


class RepairOrder(models.Model):
    _inherit = "repair.order"

    technician_ids = fields.Many2many(
        comodel_name="hr.employee",
        string="Technicians"
    )
    estimated_time = fields.Float(string="Estimated Time (hours)")

    # auto timesheet add
    analytic_account_ids = fields.One2many(
        'account.analytic.line',
        'repair_id',
        string="Analytic Account",
        copy=False
    )

    def write(self, vals):
        res = super().write(vals)

        # Trigger service line update when sale order is linked or timesheet entries change
        if vals.get('sale_order_id') or vals.get('analytic_account_ids'):
            for repair in self:
                repair._auto_add_timesheet_service()

        return res

    def _auto_add_timesheet_service(self):
        sale = self.sale_order_id
        if not sale:
            return

        # Get service product from settings
        ICP = self.env['ir.config_parameter'].sudo()
        product_id = ICP.get_param('repair_timesheet.repair_timesheet_product_id')

        if not product_id:
            return

        service_product = self.env['product.product'].browse(int(product_id))
        if not service_product.exists():
            return

        total_hours = sum(self.analytic_account_ids.mapped('unit_amount'))

        if total_hours <= 0:
            return

        # Build description with employee hours breakdown
        description_lines = [service_product.name]
        description_lines.append(f"\nEmployee Hours Breakdown:")

        # Group timesheet entries by employee
        employee_hours = {}
        for line in self.analytic_account_ids:
            employee_name = line.employee_id.name if line.employee_id else 'Unknown'
            if employee_name not in employee_hours:
                employee_hours[employee_name] = 0.0
            employee_hours[employee_name] += line.unit_amount

        for employee, hours in sorted(employee_hours.items()):
            description_lines.append(f"  - {employee}: {hours:.2f} hours")

        description_lines.append(f"\nTotal Hours: {total_hours:.2f}")

        line_description = ''.join(description_lines)

        existing_line = sale.order_line.filtered(
            lambda l: l.product_id.id == service_product.id
        )

        # Get the highest sequence number from other lines to place at bottom
        other_lines = sale.order_line.filtered(lambda l: l.product_id.id != service_product.id)
        max_sequence = max(other_lines.mapped('sequence') or [0])

        if existing_line:
            # Update existing line and move to bottom
            existing_line.write({
                'name': line_description,
                'product_uom_qty': total_hours,
                'sequence': max_sequence + 10,
            })
        else:
            # Create new line at bottom
            self.env['sale.order.line'].create({
                'order_id': sale.id,
                'product_id': service_product.id,
                'name': line_description,
                'product_uom_qty': total_hours,
                'product_uom_id': service_product.uom_id.id,
                'price_unit': service_product.lst_price,
                'sequence': max_sequence + 10,
            })

    def action_generate_technician_timesheet(self):
        for repair in self:
            for technician in repair.technician_ids:
                self.env['account.analytic.line'].create({
                    'name': f'Timesheet for Repair Order {repair.name}',
                    'employee_id': technician.id,
                    'unit_amount': repair.estimated_time or 0.0,
                    'repair_id': repair.id,
                })
