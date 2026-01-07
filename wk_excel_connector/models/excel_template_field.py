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

    @api.onchange('field_id')
    def onchange_field_id(self):
        self.name = self.field_id.field_description
