# -*- coding: utf-8 -*-
{
    'name': 'Swedish - Accounting',
    'version': '13.0.0.3',
    'summary': """Swedish chart of account EU BAS2017""",
    'description': """
This is the module to manage the accounting chart for Sweden in Odoo.
==============================================================================

Install some swedish chart of accounts.
    """,
    'author': 'Linserv AB',
    'website': 'https://www.linserv.se',
    'category': 'Localization/Account Charts',
    'depends': [
        'account',
    ],
    'data': [
        'data/account_account_tag_data.xml',
        'data/account_chart.xml',
        'data/account_tax_report_data.xml',
        'data/account_tax.xml',
        'data/account_fiscal.xml',
    ],
    'installable': True,
}
