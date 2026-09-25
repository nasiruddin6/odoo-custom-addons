{
    'name': 'NN Fund Management',
    'version': '17.0.1.0.0',
    'category': 'Finance',
    'author': 'NN Development Team',
    'website': 'https://www.example.com',
    'license': 'LGPL-3',
    'summary': 'Fund Request Management Module for Odoo 17',
    'description': '''
        This module provides comprehensive fund request management functionality.
        Features:
        - Fund request creation with auto-generated sequence numbers
        - Employee-based fund requests with approval workflow
        - Request status tracking (Draft → Submitted → Approved/Rejected)
        - PDF report generation for fund requests
        - Role-based access control (Fund User, Fund Manager)
    ''',
    'depends': [
        'base',
        'mail',
    ],
    'data': [
        # Security files
        'security/fund_groups.xml',
        'security/ir.model.access.csv',
        
        # Data files
        'data/fund_request_sequence.xml',
        
        # Views
        'views/fund_request_views.xml',
        'views/fund_request_menu.xml',
        
        # Reports
        'reports/fund_request_report_template.xml',
        'reports/fund_request_report.xml',
    ],
    'demo': [
        'data/fund_request_demo.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': True,
}
