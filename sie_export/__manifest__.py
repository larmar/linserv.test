# -*- coding: utf-8 -*-
##############################################################################
#
#    Odoo, Open Source Management Solution
#    Copyright (C) 2016-TODAY Linserv Aktiebolag, Sweden (<http://www.linserv.se>).
#
##############################################################################
{
    'name': "SIE4 Export",
    "version": "13.0.1.06",
    "author": "Linserv AB",
    "category": "Accounting",
    "summary": "SIE4 Export",
    "website": "www.linserv.se",
    "contributors": [
        'Gediminas Venclova <gediminasvenc@gmail.com>',
        'Tautvydas Banevičius <baneviciustautvydas@gmail.com>'
    ],
    "license": "",
    'depends': [
        'base', 'l10n_se', 'account_accountant'
    ],
    'description': """

        SIE4 Export

        - v12.0.1.04: Reformat invoice line description into one line
        - v13.0.1.05: lifted to v13
        - v13.0.1.06: small code fixes
        
    """,
    "demo": [],
    "data": [
        'views/account_sie_export.xml',
    ],
    "test": [],
    "js": [],
    "css": [],
    "qweb": [],
    "installable": True,
    "auto_install": False,

}