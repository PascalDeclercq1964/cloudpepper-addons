# -*- coding: utf-8 -*-
{
    'name': "Auto Translate Fields",
    'summary': "Seamlessly translate any translatable fields in Odoo across all available languages with a single click.",
    'description': """An Otoolkit app that allow you to seamlessly translate any translatable fields in Odoo across all available languages with a single click.""",
    'author': "O'Solutions Company",
    'website': "https://otoolkit.app/apps/auto-translate-fields",
    'category': 'Tools',
    'version': '18.0.0.0.3',
    'depends': ['web', 'otoolkit_auth'],
    'data': [
        "security/ir.model.access.csv",

        "views/translation_views.xml",
        "views/translation_config_views.xml",

        "wizards/bulk_translate.xml",

        "data/ir_cron.xml"
    ],
    "external_dependencies": {"python": ["requests"]},
    'assets': {
        'web.assets_backend': [
            'otoolkit_auto_translate_fields/static/src/js/translation_dialog_auto_translate.js',
            'otoolkit_auto_translate_fields/static/src/xml/translation_dialog_auto_translate.xml',
            'otoolkit_auto_translate_fields/static/src/js/json_pretty_field.js'
        ]
    },
    'maintainer': 'Tipit',
    'support': 'contact@otoolkit.app',
    'images': ['static/description/cover.gif'],
    'license': 'OPL-1',
    'installable': True,
    'application': True
}
