from odoo.http import request
from odoo import http, fields, _
from odoo.addons.portal.controllers.portal import CustomerPortal, pager as portal_pager
from odoo.exceptions import AccessError, MissingError, ValidationError


class CustomerPortalProperty(CustomerPortal):

    #==========================================================================
    # Rent Contract
    #==========================================================================
    def _prepare_rent_contracts_values(
        self, page=1, date_begin=None, date_end=None, sortby='date', **kwargs
    ):
        Contract = request.env['property.contract']
        partner = request.env.user.partner_id
        # Base domain for Rent Contracts
        domain = [
            ('partner_id', '=', partner.id),
        ]
        values = self._prepare_portal_layout_values()

        # Sorting (reuse standard portal sortings)
        searchbar_sortings = {
            'date': {'label': 'Newest', 'order': 'create_date desc'},
            'name': {'label': 'Reference', 'order': 'name asc'},
        }

        sort_order = searchbar_sortings[sortby]['order']

        # Date filter
        if date_begin and date_end:
            domain += [
                ('create_date', '>', date_begin),
                ('create_date', '<=', date_end),
            ]

        # Pager
        pager = portal_pager(
            url='/my/rent-contracts',
            total=Contract.search_count(domain),
            page=page,
            step=20,
            url_args={
                'date_begin': date_begin,
                'date_end': date_end,
                'sortby': sortby,
            },
        )

        contracts = Contract.sudo().search(
            domain,
            order=sort_order,
            limit=20,
            offset=pager['offset'],
        )
        values.update({
            'contracts': contracts,
            'page_name': 'rent_contracts',
            'pager': pager,
            'default_url': '/my/rent-contracts',
            'sortby': sortby,
            'searchbar_sortings': searchbar_sortings, 
            'date': date_begin,
        })
        return values

    @http.route(['/my/rent-contracts', '/my/rent-contracts/page/<int:page>'], type='http', auth='user', website=True)
    def portal_my_rent_contracts(self, page=1, **kwargs):
        values = self._prepare_rent_contracts_values(page=page, **kwargs)
        # Session history (optional but portal-consistent)
        request.session['my_rent_contracts_history'] = values['contracts'].ids[:100]
        return request.render('property_management_rental_sales.rent_contracts_portal_template', values)

    @http.route(['/my/rent-contracts/<int:contract_id>'],
                type='http', auth="public", website=True)
    def portal_rent_contract_page(
        self,
        contract_id,
        access_token=None,
        message=False,
        report_type=None,
        download=False,
        **kw
    ):
        try:
            contract_sudo = self._document_check_access(
                'property.contract',
                contract_id,
                access_token=access_token
            )
        except (AccessError, MissingError):
            return request.redirect('/my')

        # Report support (optional, safe to keep)
        if report_type in ('html', 'pdf', 'text'):
            return self._show_report(
                model=contract_sudo,
                report_type=report_type,
                report_ref='property_management_rental_sales.report_property_contract',  # change if needed
                download=download,
            )

        # Portal view log (optional but clean)
        if request.env.user.share and access_token:
            today = fields.Date.today().isoformat()
            session_key = f'view_contract_{contract_sudo.id}'
            if request.session.get(session_key) != today:
                request.session[session_key] = today
                contract_sudo.message_post(
                    body=_("Contract viewed by customer"),
                    message_type="notification",
                )

        backend_url = '/web#id=%s&model=property.contract&view_type=form' % contract_sudo.id

        values = {
            'contract': contract_sudo,
            'sale_order': False,  # avoid sale template conflicts
            'backend_url': backend_url,
            'message': message,
            'report_type': 'html',
            'res_company': contract_sudo.company_id,
        }

        history_session_key = 'my_rent_contracts_history'

        values = self._get_page_view_values(
            contract_sudo,
            access_token,
            values,
            history_session_key,
            False
        )

        return request.render(
            'property_management_rental_sales.rent_contract_portal_template',
            values
        )


    #==========================================================================
    # Sales Contract
    #==========================================================================
    def _prepare_sale_contracts_values(
        self, page=1, date_begin=None, date_end=None, sortby='date', **kwargs
    ):
        SaleOrder = request.env['sale.order']
        partner = request.env.user.partner_id

        # Base domain for Sale Contracts
        domain = [
            ('is_spa', '=', True),
            ('partner_id', '=', partner.id),
        ]

        # Sorting (reuse standard portal sortings)
        searchbar_sortings = {
            'date': {'label': 'Newest', 'order': 'create_date desc'},
            'name': {'label': 'Reference', 'order': 'name asc'},
        }

        sort_order = searchbar_sortings[sortby]['order']

        # Date filter
        if date_begin and date_end:
            domain += [
                ('create_date', '>', date_begin),
                ('create_date', '<=', date_end),
            ]

        # Pager
        pager = portal_pager(
            url='/my/sale-contracts',
            total=SaleOrder.search_count(domain),
            page=page,
            step=20,
            url_args={
                'date_begin': date_begin,
                'date_end': date_end,
                'sortby': sortby,
            },
        )

        orders = request.env['sale.order'].sudo().search([
            ('partner_id', '=', request.env.user.partner_id.id),
            ('is_spa', '=', True)
        ],order=sort_order, limit=20, offset=pager['offset'])

        # orders = SaleOrder.sudo().search(
        #     [],
        #     order=sort_order,
        #     limit=20,
        #     offset=pager['offset'],
        # )
        print("================== Orders in _prepare_sale_contracts_values ==================")
        print(orders)
        print("================== Orders in _prepare_sale_contracts_values ==================")
        values = {
            'orders': orders,
            'sale_order': orders[:1] if orders else False,  # First order for breadcrumb context
            'page_name': 'sale_contract',
            'pager': pager,
            'default_url': '/my/sale-contracts',
            'sortby': sortby,
            'searchbar_sortings': searchbar_sortings,
            'date': date_begin,
        }

        return values

    @http.route(
        ['/my/sale-contracts', '/my/sale-contracts/page/<int:page>'],
        type='http',
        auth='user',
        website=True
    )
    def portal_my_sale_contracts(self, page=1, **kwargs):
        values = self._prepare_sale_contracts_values(page=page, **kwargs)
        print("================== Values in portal_my_sale_contracts ==================")
        print(values)
        print("================== Values in portal_my_sale_contracts ==================")

        # Session history (optional but portal-consistent)
        request.session['my_sale_contracts_history'] = values['orders'].ids[:100]

        return request.render('property_management_rental_sales.sales_contracts_portal_template', values)
        

    def _prepare_home_portal_values(self, counters):
        values = super()._prepare_home_portal_values(counters)
        spa_count = request.env['sale.order'].sudo().search_count([
            ('partner_id', '=', request.env.user.partner_id.id),
            ('is_spa', '=', True)
        ])
        
        rent_count = request.env['property.contract'].sudo().search_count([
            ('partner_id', '=', request.env.user.partner_id.id)
        ])

        values.update({
            'rent_count': rent_count,
            'spa_count': spa_count,
        })
        return values
    
    def counters(self, counters, **kw):
        cache = (request.session.portal_counters or {}).copy()
        res = self._prepare_home_portal_values(counters)
        cache.update({k: bool(v) for k, v in res.items() if k.endswith('_count')})
        return res