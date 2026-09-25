from odoo import api, fields, models, _
from odoo.exceptions import UserError
from dateutil.relativedelta import relativedelta
import io
import base64
import xlsxwriter


class LeaveSummaryWizard(models.TransientModel):
    _name = 'leave.summary.wizard'
    _description = 'Employee Leave Summary Report Wizard'

    def _get_default_date_from(self):
        return fields.Date.context_today(self).replace(day=1)

    def _get_default_date_to(self):
        first_day = fields.Date.context_today(self).replace(day=1)
        return first_day + relativedelta(months=1, days=-1)

    date_from = fields.Date(string='From Date', required=True, default=_get_default_date_from)
    date_to = fields.Date(string='To Date', required=True, default=_get_default_date_to)
    employee_ids = fields.Many2many('hr.employee', string='Employees', required=True)
    status = fields.Selection([
        ('confirm', 'To Approve'),
        ('validate1', 'Second Approval'),
        ('validate', 'Approved'),
        ('refuse', 'Refused'),
        ('cancel', 'Cancelled'),
        ('all', 'All')
    ], string='Status', default='all', required=True)
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company)

    @api.constrains('date_from', 'date_to')
    def _check_dates(self):
        for wizard in self:
            if wizard.date_from > wizard.date_to:
                raise UserError(_('From Date must be earlier than To Date.'))

    def action_export_excel(self):
        self.ensure_one()

        if not self.employee_ids:
            raise UserError(_('Please select at least one employee.'))

        leave_data = self._get_leave_data()
        excel_file = self._generate_excel_report(leave_data)

        filename = f'Employee_Leave_Summary_{self.date_from.strftime("%Y%m%d")}_to_{self.date_to.strftime("%Y%m%d")}.xlsx'

        attachment = self.env['ir.attachment'].create({
            'name': filename,
            'type': 'binary',
            'datas': base64.b64encode(excel_file),
            'mimetype': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        })

        return {
            'type': 'ir.actions.act_url',
            'url': f'/web/content/{attachment.id}?download=true',
            'target': 'new',
        }

    def _get_leave_data(self):
        domain = [
            ('employee_id', 'in', self.employee_ids.ids),
            ('date_from', '<=', self.date_to),
            ('date_to', '>=', self.date_from),
        ]

        if self.status != 'all':
            domain.append(('state', '=', self.status))

        leaves = self.env['hr.leave'].search(domain, order='employee_id, date_from')

        leave_data = []
        for leave in leaves:
            leave_balance = self._get_leave_balance(leave.employee_id, leave.holiday_status_id)

            leave_data.append({
                'badge_id': leave.employee_id.barcode or '',
                'employee': leave.employee_id.name,
                'department': leave.employee_id.department_id.name or '',
                'date_from': leave.date_from.strftime('%d-%m-%Y') if leave.date_from else '',
                'date_to': leave.date_to.strftime('%d-%m-%Y') if leave.date_to else '',
                'leave_type': leave.holiday_status_id.name,
                'total_days': leave.number_of_days,
                'leave_balance': leave_balance,
                'status': dict(leave._fields['state'].selection).get(leave.state, ''),
            })

        return leave_data

    def _get_leave_balance(self, employee, leave_type):
        allocation = self.env['hr.leave.allocation'].search([
            ('employee_id', '=', employee.id),
            ('holiday_status_id', '=', leave_type.id),
            ('state', '=', 'validate')
        ], limit=1, order='date_from desc')

        if allocation:
            return allocation.number_of_days - allocation.leaves_taken
        return 0.0

    def _generate_excel_report(self, leave_data):
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        worksheet = workbook.add_worksheet('Leave Summary')

        formats = self._get_excel_formats(workbook)

        row = 0
        row = self._write_company_header(worksheet, formats, row)
        row = self._write_report_title(worksheet, formats, row)
        row = self._write_table_headers(worksheet, formats, row)
        self._write_leave_data(worksheet, formats, leave_data, row)

        self._set_column_widths(worksheet)

        workbook.close()
        output.seek(0)
        return output.read()

    def _get_excel_formats(self, workbook):
        return {
            'title': workbook.add_format({
                'bold': True,
                'font_size': 16,
                'align': 'center',
                'valign': 'vcenter',
                'font_color': '#1F497D',
                'border': 1
            }),
            'header': workbook.add_format({
                'bold': True,
                'font_size': 12,
                'align': 'center',
                'valign': 'vcenter',
                'bg_color': '#4472C4',
                'font_color': 'white',
                'border': 1,
                'text_wrap': True
            }),
            'cell': workbook.add_format({
                'font_size': 11,
                'align': 'left',
                'valign': 'vcenter',
                'border': 1,
                'text_wrap': True
            }),
            'cell_center': workbook.add_format({
                'font_size': 11,
                'align': 'center',
                'valign': 'vcenter',
                'border': 1
            }),
            'number': workbook.add_format({
                'font_size': 11,
                'align': 'center',
                'valign': 'vcenter',
                'border': 1,
                'num_format': '0.00'
            }),
            'company': workbook.add_format({
                'font_size': 12,
                'align': 'center',
                'valign': 'vcenter',
                'bold': True
            }),
            'info': workbook.add_format({
                'font_size': 10,
                'align': 'center',
                'valign': 'vcenter'
            })
        }

    def _write_company_header(self, worksheet, formats, row):
        worksheet.merge_range(row, 0, row, 8, self.company_id.name or 'Company Name', formats['company'])
        row += 1

        address_parts = [
            self.company_id.street,
            self.company_id.street2,
            self.company_id.city,
            self.company_id.state_id.name if self.company_id.state_id else None,
            self.company_id.zip,
            self.company_id.country_id.name if self.company_id.country_id else None
        ]
        address = ', '.join(filter(None, address_parts)) or 'Address'
        worksheet.merge_range(row, 0, row, 8, address, formats['info'])
        row += 1

        contact_parts = []
        if self.company_id.phone:
            contact_parts.append(f'Phone: {self.company_id.phone}')
        if self.company_id.website:
            contact_parts.append(f'Website: {self.company_id.website}')
        contact = ' | '.join(contact_parts) or 'Phone and website'
        worksheet.merge_range(row, 0, row, 8, contact, formats['info'])
        row += 2

        return row

    def _write_report_title(self, worksheet, formats, row):
        worksheet.merge_range(row, 0, row, 8, 'Employee Leave Summary Report', formats['title'])
        worksheet.set_row(row, 25)
        return row + 2

    def _write_table_headers(self, worksheet, formats, row):
        headers = [
            'Badge ID', 'Employee', 'Department', 'Start Date', 'End Date',
            'Leave Type', 'Total Leave', 'Leave Balance', 'Status'
        ]
        for col, header in enumerate(headers):
            worksheet.write(row, col, header, formats['header'])
        return row + 1

    def _write_leave_data(self, worksheet, formats, leave_data, start_row):
        row = start_row
        for leave in leave_data:
            worksheet.write(row, 0, leave['badge_id'], formats['cell_center'])
            worksheet.write(row, 1, leave['employee'], formats['cell'])
            worksheet.write(row, 2, leave['department'], formats['cell'])
            worksheet.write(row, 3, leave['date_from'], formats['cell_center'])
            worksheet.write(row, 4, leave['date_to'], formats['cell_center'])
            worksheet.write(row, 5, leave['leave_type'], formats['cell'])
            worksheet.write(row, 6, leave['total_days'], formats['number'])
            worksheet.write(row, 7, leave['leave_balance'], formats['number'])
            worksheet.write(row, 8, leave['status'], formats['cell_center'])
            row += 1

    def _set_column_widths(self, worksheet):
        column_widths = [12, 25, 20, 15, 15, 25, 12, 15, 15]
        for col, width in enumerate(column_widths):
            worksheet.set_column(col, col, width)
