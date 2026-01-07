# -*- coding: utf-8 -*-
##########################################################################
# Author      : Webkul Software Pvt. Ltd. (<https://webkul.com/>)
# Copyright(c): 2015-Present Webkul Software Pvt. Ltd.
# All Rights Reserved.
#
#
#
# This program is copyright property of the author mentioned above.
# You can`t redistribute it and/or modify it.
#
#
# You should have received a copy of the License along with this program.
# If not, see <https://store.webkul.com/license.html/>
##########################################################################

{
    'name': 'Excel Odoo Connector',
    'version': '6.0.0',
    'category': 'Accounting',
    'author': 'Webkul Software Pvt. Ltd.',
    'website': 'https://store.webkul.com/odoo-excel-connector.html',
    'sequence': 1,
    'summary': "Odoo Excel Connector integrates your Odoo to Excel. It allows syncing data from Odoo to Excel or LibreOffice.PowerBI Connector for Odoo Data, Odoo Excel Data Connector, Excel Report Connector, All In One Excel Report, Sales Order Excel Report, Invoice Excel Report, Delivery Order Report, XLSX Report, Odoo LibreOffice Connector, big data connector, tableau connector.",
    "license":  "Other proprietary",
    'live_test_url': 'https://odoodemo.webkul.com/?module=wk_excel_connector',
    'description': """
This Brilliant Module will Connect Odoo with MS Excel, LibreOffice and Synchronise Data.
    """,
    'depends': [
        'mail'
    ],
    'data': [
        'views/excel_template.xml',
        'views/menu.xml',
        'security/security.xml',
        'security/ir.model.access.csv'
    ],
    "images": ['static/description/banner.png'],
    'application': True,
    'installable': True,
    'auto_install': False,
    'currency': 'USD',
    'price': 49,
    'pre_init_hook': 'pre_init_check'
}
