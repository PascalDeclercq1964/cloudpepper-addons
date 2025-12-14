# -*- coding: utf-8 -*-
{
    'name': "Hide Price & Show Contact Us for Public Users",
    'version': '1.0.1',
    'category': 'Website',
    'summary': """Hide product prices and replace buy button with contact us for non-logged users""",
    'description': """This module hides product prices for non-logged users and 
    replaces the buy button with a contact us button.""",
    'author': 'Akshar Group Technologies',
    'website': 'https://www.akshargrouptechnologies.com/',
    'depends': ['website_sale'],
    'images': ['static/description/hideprice.png'],
    "icon": "static/description/icon.png",
     'data': [
        'views/shop_templates.xml',     
        'views/product_templates.xml',   
    ],
    "license": "OPL-1",
    'installable': True,
    'auto_install': False,
    'application': False,

}


