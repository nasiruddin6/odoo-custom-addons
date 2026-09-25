# -*- coding: utf-8 -*-

import base64
from datetime import datetime
from io import BytesIO
from datetime import datetime, time

try:
    import xlsxwriter
except ImportError:
    xlsxwriter = None

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError


class FSNAnalysisWizard(models.TransientModel):
    """
    FSN Analysis Wizard

    This wizard allows users to configure and generate FSN (Fast, Slow, Non-Moving)
    analysis reports with various filtering options.
    """
    _name = 'fsn.analysis.wizard'
    _description = 'FSN Analysis Wizard'

    # Date Range
    start_date = fields.Date(
        string='Start Date',
        required=True,
        default=lambda self: fields.Date.today().replace(month=1, day=1),
        help='Start date for the analysis period'
    )
    end_date = fields.Date(
        string='End Date',
        required=True,
        default=fields.Date.today,
        help='End date for the analysis period'
    )

    # Classification Filter
    classification_type = fields.Selection([
        ('all', 'All'),
        ('fast', 'Fast Moving'),
        ('slow', 'Slow Moving'),
        ('non_moving', 'Non Moving'),
    ], string='Classification Type', required=True, default='all',
        help='Filter results by FSN classification type')

    # Product Filters
    product_ids = fields.Many2many(
        'product.product',
        string='Products',
        domain=[('type', '!=', 'service')],
        help='Leave empty to analyze all products'
    )
    product_categ_ids = fields.Many2many(
        'product.category',
        string='Product Categories',
        help='Filter products by categories'
    )

    # Warehouse & Company
    warehouse_ids = fields.Many2many(
        'stock.warehouse',
        string='Warehouses',
        help='Leave empty to analyze all warehouses'
    )
    company_id = fields.Many2one(
        'res.company',
        string='Company',
        required=True,
        default=lambda self: self.env.company,
        help='Company for analysis'
    )

    # Editable Thresholds
    fast_threshold = fields.Float(
        string='Fast Moving Threshold',
        default=lambda self: self.env['fsn.analysis.report'].get_fsn_thresholds()[0],
        required=True,
        help='Products with movement >= this value are classified as Fast Moving'
    )
    slow_threshold = fields.Float(
        string='Slow Moving Threshold',
        default=lambda self: self.env['fsn.analysis.report'].get_fsn_thresholds()[1],
        required=True,
        help='Products with movement >= this value are classified as Slow Moving'
    )

    @api.constrains('fast_threshold', 'slow_threshold')
    def _check_thresholds(self):
        """Validate that fast threshold is greater than slow threshold"""
        for wizard in self:
            if wizard.fast_threshold <= wizard.slow_threshold:
                raise ValidationError(_(
                    'Fast Moving Threshold (%.2f) must be greater than Slow Moving Threshold (%.2f)!'
                ) % (wizard.fast_threshold, wizard.slow_threshold))
            if wizard.fast_threshold <= 0 or wizard.slow_threshold <= 0:
                raise ValidationError(_('Thresholds must be greater than zero!'))

    @api.constrains('start_date', 'end_date')
    def _check_dates(self):
        """Validate date range"""
        for wizard in self:
            if wizard.start_date > wizard.end_date:
                raise ValidationError(_('Start Date cannot be later than End Date!'))

    def action_generate_analysis(self):
        """
        Generate FSN Analysis and open the result view

        Returns:
            dict: Action to open FSN analysis report
        """
        self.ensure_one()

        # Prepare parameters
        product_ids = self.product_ids.ids if self.product_ids else None
        categ_ids = self.product_categ_ids.ids if self.product_categ_ids else None
        warehouse_ids = self.warehouse_ids.ids if self.warehouse_ids else None

        # Generate analysis
        FSNReport = self.env['fsn.analysis.report']
        end_datetime = datetime.combine(self.end_date, time.max)
        records = FSNReport.generate_fsn_analysis(
            date_from=self.start_date,
            date_to=end_datetime,
            product_ids=product_ids,
            categ_ids=categ_ids,
            warehouse_ids=warehouse_ids,
            company_id=self.company_id.id,
            fast_threshold=self.fast_threshold,
            slow_threshold=self.slow_threshold
        )

        if not records:
            raise UserError(_('No data found for the selected criteria!'))

        # Apply classification filter
        domain = [
            ('date_from', '=', self.start_date),
            ('date_to', '=', self.end_date),
            ('company_id', '=', self.company_id.id),
        ]

        if self.classification_type != 'all':
            domain.append(('fsn_classification', '=', self.classification_type))

        # Return action to open analysis results
        return {
            'name': _('FSN Analysis Report'),
            'type': 'ir.actions.act_window',
            'res_model': 'fsn.analysis.report',
            'view_mode': 'tree,pivot,graph',
            'domain': domain,
            'context': {
                'search_default_group_by_classification': 1,
                'search_default_group_by_category': 1,
            },
            'target': 'current',
        }

    def action_export_excel(self):
        """
        Export FSN Analysis to Excel

        Returns:
            dict: Action to download Excel file
        """
        self.ensure_one()

        if not xlsxwriter:
            raise UserError(_(
                'The xlsxwriter Python library is required to export Excel files. '
                'Please install it using: pip install xlsxwriter'
            ))

        # Generate analysis first
        product_ids = self.product_ids.ids if self.product_ids else None
        categ_ids = self.product_categ_ids.ids if self.product_categ_ids else None
        warehouse_ids = self.warehouse_ids.ids if self.warehouse_ids else None

        FSNReport = self.env['fsn.analysis.report']
        records = FSNReport.generate_fsn_analysis(
            date_from=self.start_date,
            date_to=self.end_date,
            product_ids=product_ids,
            categ_ids=categ_ids,
            warehouse_ids=warehouse_ids,
            company_id=self.company_id.id,
            fast_threshold=self.fast_threshold,
            slow_threshold=self.slow_threshold
        )

        # Apply classification filter
        if self.classification_type != 'all':
            records = records.filtered(
                lambda r: r.fsn_classification == self.classification_type
            )

        if not records:
            raise UserError(_('No data found for the selected criteria!'))

        # Generate Excel file
        output = BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})

        # Create FSN Analysis sheet
        self._create_fsn_analysis_sheet(workbook, records)

        # Create Non-Moving Products sheet if applicable
        non_moving_records = records.filtered(
            lambda r: r.fsn_classification == 'non_moving'
        )
        if non_moving_records:
            self._create_non_moving_sheet(workbook, non_moving_records)

        workbook.close()
        output.seek(0)

        # Encode file content
        excel_file = base64.b64encode(output.read())
        output.close()

        # Create attachment
        filename = f'FSN_Analysis_{self.start_date}_{self.end_date}.xlsx'
        attachment = self.env['ir.attachment'].create({
            'name': filename,
            'type': 'binary',
            'datas': excel_file,
            'res_model': self._name,
            'res_id': self.id,
            'mimetype': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        })

        # Return download action
        return {
            'type': 'ir.actions.act_url',
            'url': f'/web/content/{attachment.id}?download=true',
            'target': 'new',
        }

    def _create_fsn_analysis_sheet(self, workbook, records):
        """
        Create FSN Analysis worksheet

        Args:
            workbook: xlsxwriter Workbook object
            records: FSN analysis records
        """
        worksheet = workbook.add_worksheet('FSN Analysis')

        # Define formats
        header_format = workbook.add_format({
            'bold': True,
            'bg_color': '#4472C4',
            'font_color': 'white',
            'border': 1,
            'align': 'center',
            'valign': 'vcenter',
            'text_wrap': True,
        })

        cell_format = workbook.add_format({
            'border': 1,
            'align': 'left',
            'valign': 'vcenter',
        })

        number_format = workbook.add_format({
            'border': 1,
            'align': 'right',
            'valign': 'vcenter',
            'num_format': '#,##0.00',
        })

        date_format = workbook.add_format({
            'border': 1,
            'align': 'center',
            'valign': 'vcenter',
            'num_format': 'yyyy-mm-dd hh:mm:ss',
        })

        fast_format = workbook.add_format({
            'border': 1,
            'bg_color': '#C6EFCE',
            'font_color': '#006100',
            'bold': True,
            'align': 'center',
        })

        # Slow moving format (yellow)
        slow_format = workbook.add_format({
            'border': 1,
            'bg_color': '#FFEB9C',
            'font_color': '#9C6500',
            'bold': True,
            'align': 'center',
        })

        # Non-moving format (red)
        non_moving_format = workbook.add_format({
            'border': 1,
            'bg_color': '#FFC7CE',
            'font_color': '#9C0006',
            'bold': True,
            'align': 'center',
        })

        headers = [
            'Product Code',
            'Product Name',
            'Product Category',
            'Warehouse',
            'Company',
            'Quantity Moved',
            'UoM',
            'On Hand Qty',
            'FSN Classification',
            'Last Movement Date',
        ]

        title_format = workbook.add_format({
            'bold': True,
            'font_size': 16,
            'align': 'center',
            'valign': 'vcenter',
        })

        company_format = workbook.add_format({
            'bold': True,
            'font_size': 11,
            'align': 'left',
        })

        info_format = workbook.add_format({
            'font_size': 10,
            'align': 'center',
        })

        date_info_format = workbook.add_format({
            'font_size': 10,
            'align': 'right',
        })

        # ==============================
        # Top Company & Report Info
        # ==============================

        company = self.company_id

        worksheet.merge_range('A1:K1', company.name or '', title_format)
        worksheet.merge_range(
            'A2:K2',
            company.partner_id.contact_address or '',
            info_format
        )

        worksheet.merge_range(
            'A3:K3',
            f"Email: {company.email or ''} | Phone: {company.phone or ''} | Website: {company.website or ''}",
            info_format
        )

        worksheet.merge_range('A5:K5', 'FSN Analysis Report', title_format)

        worksheet.merge_range(
            'A7:D7',
            f"Analysis Period: {self.start_date} To {self.end_date}",
            company_format
        )

        worksheet.merge_range(
            'H7:J7',
            f"Generated On: {fields.Date.today()}",
            date_info_format
        )

        table_start_row = 8

        for col, header in enumerate(headers):
            worksheet.write(table_start_row, col, header, header_format)

        # Set column widths
        worksheet.set_column(0, 0, 15)  # Product Code
        worksheet.set_column(1, 1, 30)  # Product Name
        worksheet.set_column(2, 2, 20)  # Category
        worksheet.set_column(3, 3, 20)  # Warehouse
        worksheet.set_column(4, 4, 20)  # Company
        worksheet.set_column(5, 5, 15)  # Qty Moved
        worksheet.set_column(6, 6, 10)  # UoM
        worksheet.set_column(7, 7, 15)  # On Hand
        worksheet.set_column(8, 8, 18)  # Classification
        worksheet.set_column(9, 9, 20)  # Last Movement

        # Write data
        row = table_start_row + 1

        for record in records.sorted(key=lambda r: (-r.qty_moved, r.product_id.name)):
            # Determine classification format
            if record.fsn_classification == 'fast':
                classification_format = fast_format
                classification_text = 'Fast Moving'
            elif record.fsn_classification == 'slow':
                classification_format = slow_format
                classification_text = 'Slow Moving'
            else:
                classification_format = non_moving_format
                classification_text = 'Non Moving'

            worksheet.write(row, 0, record.product_code or '', cell_format)
            worksheet.write(row, 1, record.product_id.name, cell_format)
            worksheet.write(row,2,record.product_categ_id.complete_name if record.product_categ_id else '',cell_format)
            worksheet.write(row, 3, record.warehouse_id.name, cell_format)
            worksheet.write(row, 4, record.company_id.name, cell_format)
            worksheet.write(row, 5, record.qty_moved, number_format)
            worksheet.write(row, 6, record.uom_id.name, cell_format)
            worksheet.write(row, 7, record.on_hand_qty, number_format)
            worksheet.write(row, 8, classification_text, classification_format)

            if record.last_movement_date:
                worksheet.write_datetime(row, 9, record.last_movement_date, date_format)
            else:
                worksheet.write(row, 9, 'No Movement', cell_format)

            row += 1

        # Add autofilter
        worksheet.autofilter(0, 0, row - 1, len(headers) - 1)

    def _create_non_moving_sheet(self, workbook, records):
        """
        Create Non-Moving Products worksheet

        Args:
            workbook: xlsxwriter Workbook object
            records: Non-moving product records
        """
        worksheet = workbook.add_worksheet('Non-Moving Products')

        # Define formats
        header_format = workbook.add_format({
            'bold': True,
            'bg_color': '#9C0006',
            'font_color': 'white',
            'border': 1,
            'align': 'center',
            'valign': 'vcenter',
            'text_wrap': True,
        })

        cell_format = workbook.add_format({
            'border': 1,
            'align': 'left',
            'valign': 'vcenter',
        })

        number_format = workbook.add_format({
            'border': 1,
            'align': 'right',
            'valign': 'vcenter',
            'num_format': '#,##0.00',
        })

        date_format = workbook.add_format({
            'border': 1,
            'align': 'center',
            'valign': 'vcenter',
            'num_format': 'yyyy-mm-dd hh:mm:ss',
        })

        # Write header
        headers = [
            'Product Code',
            'Product Name',
            'Product Category',
            'Warehouse',
            'On Hand Quantity',
            'UoM',
            'Last Movement Date',
            'Days Since Last Movement',
        ]

        for col, header in enumerate(headers):
            worksheet.write(0, col, header, header_format)

        # Set column widths
        worksheet.set_column(0, 0, 15)  # Product Code
        worksheet.set_column(1, 1, 35)  # Product Name
        worksheet.set_column(2, 2, 25)  # Category
        worksheet.set_column(3, 3, 20)  # Warehouse
        worksheet.set_column(4, 4, 18)  # On Hand
        worksheet.set_column(5, 5, 10)  # UoM
        worksheet.set_column(6, 6, 20)  # Last Movement
        worksheet.set_column(7, 7, 25)  # Days Since

        # Write data
        row = 1
        today = fields.Date.today()

        for record in records.sorted(key=lambda r: r.product_id.name):
            worksheet.write(row, 0, record.product_code or '', cell_format)
            worksheet.write(row, 1, record.product_id.name, cell_format)
            worksheet.write(row, 2, record.product_categ_id.complete_name if record.product_categ_id else None, cell_format)
            worksheet.write(row, 3, record.warehouse_id.name, cell_format)
            worksheet.write(row, 4, record.on_hand_qty, number_format)
            worksheet.write(row, 5, record.uom_id.name, cell_format)

            if record.last_movement_date:
                worksheet.write_datetime(row, 6, record.last_movement_date, date_format)
                days_since = (today - record.last_movement_date.date()).days
                worksheet.write(row, 7, days_since, cell_format)
            else:
                worksheet.write(row, 6, 'No Movement', cell_format)
                worksheet.write(row, 7, 'N/A', cell_format)

            row += 1

        # Freeze header row
        worksheet.freeze_panes(1, 0)

        # Add autofilter
        worksheet.autofilter(0, 0, row - 1, len(headers) - 1)
