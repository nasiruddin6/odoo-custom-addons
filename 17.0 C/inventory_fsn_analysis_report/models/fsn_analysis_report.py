# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError


class FSNAnalysisReport(models.Model):
    """
    FSN Analysis Report Model

    This model stores the results of FSN (Fast, Slow, Non-Moving) analysis
    for stock items based on movement data within a specified date range.
    """
    _name = 'fsn.analysis.report'
    _description = 'FSN Analysis Report'
    _order = 'qty_moved desc, product_id'
    _rec_name = 'product_id'

    # Core Fields
    product_id = fields.Many2one(
        'product.product',
        string='Product',
        required=True,
        index=True,
        ondelete='cascade'
    )
    product_categ_id = fields.Many2one(
        'product.category',
        string='Product Category',
        related='product_id.categ_id',
        store=True,
        index=True
    )
    warehouse_id = fields.Many2one(
        'stock.warehouse',
        string='Warehouse',
        required=True,
        index=True,
        ondelete='cascade'
    )
    company_id = fields.Many2one(
        'res.company',
        string='Company',
        required=True,
        index=True,
        default=lambda self: self.env.company
    )

    # Analysis Data
    qty_moved = fields.Float(
        string='Quantity Moved',
        digits='Product Unit of Measure',
        help='Total quantity moved during the analysis period'
    )
    fsn_classification = fields.Selection([
        ('fast', 'Fast Moving'),
        ('slow', 'Slow Moving'),
        ('non_moving', 'Non Moving'),
    ], string='FSN Classification', required=True, index=True)

    # Date Range
    date_from = fields.Date(
        string='Date From',
        required=True,
        index=True
    )
    date_to = fields.Date(
        string='Date To',
        required=True,
        index=True
    )

    # Additional Information
    uom_id = fields.Many2one(
        'uom.uom',
        string='Unit of Measure',
        related='product_id.uom_id',
        store=True
    )
    on_hand_qty = fields.Float(
        string='On Hand Quantity',
        digits='Product Unit of Measure',
        help='Current stock on hand at the time of analysis'
    )
    last_movement_date = fields.Datetime(
        string='Last Movement Date',
        help='Date of the last stock movement for this product'
    )
    product_code = fields.Char(
        string='Internal Reference',
        related='product_id.default_code',
        store=True
    )

    _sql_constraints = [
        ('unique_analysis_record',
         'unique(product_id, warehouse_id, company_id, date_from, date_to)',
         'Analysis record must be unique per product, warehouse, company and date range!')
    ]

    def name_get(self):
        """Custom name_get to display product name with FSN classification"""
        result = []
        for record in self:
            classification_label = dict(self._fields['fsn_classification'].selection).get(
                record.fsn_classification, ''
            )
            name = f"{record.product_id.display_name} - {classification_label}"
            result.append((record.id, name))
        return result

    @api.model
    def get_fsn_thresholds(self):
        """
        Get FSN classification thresholds from system parameters

        Returns:
            tuple: (fast_threshold, slow_threshold)
        """
        IrConfigParameter = self.env['ir.config_parameter'].sudo()

        fast_threshold = float(
            IrConfigParameter.get_param(
                'inventory_fsn_analysis.fast_threshold',
                default=100.0
            )
        )
        slow_threshold = float(
            IrConfigParameter.get_param(
                'inventory_fsn_analysis.slow_threshold',
                default=10.0
            )
        )

        return fast_threshold, slow_threshold

    @api.model
    def classify_product(self, qty_moved, fast_threshold=None, slow_threshold=None):
        """
        Classify product based on quantity moved

        Args:
            qty_moved (float): Quantity moved during analysis period
            fast_threshold (float): Optional custom fast moving threshold
            slow_threshold (float): Optional custom slow moving threshold

        Returns:
            str: FSN classification ('fast', 'slow', or 'non_moving')
        """
        if fast_threshold is None or slow_threshold is None:
            fast_threshold, slow_threshold = self.get_fsn_thresholds()

        if qty_moved >= fast_threshold:
            return 'fast'
        elif qty_moved >= slow_threshold:
            return 'slow'
        else:
            return 'non_moving'

    @api.model
    def generate_fsn_analysis(self, date_from, date_to, product_ids=None,
                             categ_ids=None, warehouse_ids=None, company_id=None,
                             fast_threshold=None, slow_threshold=None):
        """
        Generate FSN Analysis Report

        Args:
            date_from (date): Start date for analysis
            date_to (date): End date for analysis
            product_ids (list): List of product IDs to analyze
            categ_ids (list): List of category IDs to filter
            warehouse_ids (list): List of warehouse IDs to analyze
            company_id (int): Company ID
            fast_threshold (float): Optional custom fast moving threshold
            slow_threshold (float): Optional custom slow moving threshold

        Returns:
            recordset: FSN Analysis Report records
        """
        if not company_id:
            company_id = self.env.company.id

        # Clear existing analysis for this date range
        existing_records = self.search([
            ('date_from', '=', date_from),
            ('date_to', '=', date_to),
            ('company_id', '=', company_id),
        ])
        if existing_records:
            existing_records.unlink()

        # Build domain for stock moves
        domain = [
            ('state', '=', 'done'),
            ('date', '>=', date_from),
            ('date', '<=', date_to),
            ('company_id', '=', company_id),
        ]

        # Apply filters
        if product_ids:
            domain.append(('product_id', 'in', product_ids))
        if categ_ids:
            domain.append(('product_id.categ_id', 'in', categ_ids))

        # Get stock moves
        stock_moves = self.env['stock.move'].search(domain)

        # Get warehouses
        if warehouse_ids:
            warehouses = self.env['stock.warehouse'].browse(warehouse_ids)
        else:
            warehouses = self.env['stock.warehouse'].search([
                ('company_id', '=', company_id)
            ])

        # Prepare data structure for analysis
        analysis_data = {}

        for move in stock_moves:
            # Determine warehouse from location
            warehouse = self._get_warehouse_from_location(
                move.location_id, move.location_dest_id, warehouses
            )

            if not warehouse:
                continue

            key = (move.product_id.id, warehouse.id)

            if key not in analysis_data:
                analysis_data[key] = {
                    'product_id': move.product_id.id,
                    'warehouse_id': warehouse.id,
                    'qty_moved': 0.0,
                    'last_movement_date': move.date,
                }

            # Accumulate quantity moved
            analysis_data[key]['qty_moved'] += move.product_uom_qty

            # Update last movement date
            if move.date > analysis_data[key]['last_movement_date']:
                analysis_data[key]['last_movement_date'] = move.date

        # Handle products with no movement (Non-Moving)
        if product_ids:
            products = self.env['product.product'].browse(product_ids)
        elif categ_ids:
            products = self.env['product.product'].search([
                ('categ_id', 'in', categ_ids),
                ('type', '=', 'product'),
            ])
        else:
            products = self.env['product.product'].search([
                ('type', '=', 'product'),
            ])

        # Add non-moving products
        for product in products:
            for warehouse in warehouses:
                key = (product.id, warehouse.id)
                if key not in analysis_data:
                    # Get last movement date for this product
                    last_move = self.env['stock.move'].search([
                        ('product_id', '=', product.id),
                        ('state', '=', 'done'),
                    ], order='date desc', limit=1)

                    analysis_data[key] = {
                        'product_id': product.id,
                        'warehouse_id': warehouse.id,
                        'qty_moved': 0.0,
                        'last_movement_date': last_move.date if last_move else False,
                    }

        # Create FSN analysis records
        records_to_create = []
        for key, data in analysis_data.items():
            product = self.env['product.product'].browse(data['product_id'])
            warehouse = self.env['stock.warehouse'].browse(data['warehouse_id'])

            # Get on-hand quantity
            on_hand_qty = product.with_context(
                warehouse=warehouse.id,
                location=warehouse.lot_stock_id.id
            ).qty_available

            # Classify product
            classification = self.classify_product(
                data['qty_moved'],
                fast_threshold=fast_threshold,
                slow_threshold=slow_threshold
            )

            records_to_create.append({
                'product_id': data['product_id'],
                'warehouse_id': data['warehouse_id'],
                'company_id': company_id,
                'qty_moved': data['qty_moved'],
                'fsn_classification': classification,
                'date_from': date_from,
                'date_to': date_to,
                'on_hand_qty': on_hand_qty,
                'last_movement_date': data['last_movement_date'],
            })

        # Batch create records
        if records_to_create:
            return self.create(records_to_create)
        else:
            return self.env['fsn.analysis.report']

    def _get_warehouse_from_location(self, location_src, location_dest, warehouses):
        """
        Determine warehouse from source and destination locations

        Args:
            location_src: Source location
            location_dest: Destination location
            warehouses: Warehouses to consider

        Returns:
            stock.warehouse: Warehouse record or False
        """
        for warehouse in warehouses:
            # Check if movement involves warehouse stock location
            if (location_src.id == warehouse.lot_stock_id.id or
                location_dest.id == warehouse.lot_stock_id.id or
                warehouse.lot_stock_id.id in location_src.parent_path.split('/') or
                warehouse.lot_stock_id.id in location_dest.parent_path.split('/')):
                return warehouse
        return False

    def action_view_stock_moves(self):
        """Open stock moves related to this analysis record"""
        self.ensure_one()

        action = self.env['ir.actions.act_window']._for_xml_id(
            'stock.stock_move_action'
        )
        action['domain'] = [
            ('product_id', '=', self.product_id.id),
            ('state', '=', 'done'),
            ('date', '>=', self.date_from),
            ('date', '<=', self.date_to),
        ]
        action['context'] = {
            'search_default_product_id': self.product_id.id,
        }
        return action

