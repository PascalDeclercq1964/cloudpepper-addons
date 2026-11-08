# -*- coding: utf-8 -*-
##########################################################################
#
#   Copyright (c) 2015-Present Webkul Software Pvt. Ltd. (<https://webkul.com/>)
#   See LICENSE file for full copyright and licensing details.
#   License URL : <https://store.webkul.com/license.html/>
#
##########################################################################

from odoo import api, models, fields

class ExcelTemplateField(models.Model):
    _name = "excel.template.field"
    _description = "Excel Template Fields"

    name = fields.Char("Name/Label")
    excel_template_id = fields.Many2one(
        comodel_name = "excel.template",
        string = "Excel Template"
    )
    model = fields.Char("Model", related="excel_template_id.model_name")
    field_id = fields.Many2one(
        "ir.model.fields",
        string = "Field",
        domain = '[("model", "=", model)]',
    )
    sequence = fields.Integer("Sequence")

    # --- AANPASSING Chameleonstars: kolommen uitklappen ---
    expand_mode = fields.Selection(
        [
            ('json', 'JSON-object: kolom per sleutel'),
            ('html_list', 'HTML-lijst: kolom per item'),
        ],
        string="Uitklappen",
        help="Leeg: gewone kolom.\n"
             "JSON-object: bv. Product Properties wordt prop_brand, prop_colors, ...\n"
             "HTML-lijst: de opsommingspunten van een beschrijving worden bullet_fr_1, bullet_fr_2, ...",
    )
    expand_prefix = fields.Char(
        "Kolomprefix",
        help="Begin van de kolomnamen, bv. prop_ of bullet_fr_. Leeg = naam van deze regel.",
    )
    expand_max = fields.Integer(
        "Max. kolommen",
        help="Alleen voor HTML-lijst. 0 = zoveel als nodig. "
             "Met een vast getal (bv. 5) bestaan de kolommen altijd, ook als ze leeg zijn.",
    )

    @api.onchange('field_id')
    def onchange_field_id(self):
        self.name = self.field_id.field_description
