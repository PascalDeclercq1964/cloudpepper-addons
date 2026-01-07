# -*- coding: utf-8 -*-
##########################################################################
#
#   Copyright (c) 2015-Present Webkul Software Pvt. Ltd. (<https://webkul.com/>)
#   See LICENSE file for full copyright and licensing details.
#   License URL : <https://store.webkul.com/license.html/>
#
##########################################################################

import uuid
from odoo import models, fields, api
import logging

_logger = logging.getLogger(__name__)

class ExcelTemplate(models.Model):
    _name = "excel.template"
    _description = "Excel Template"
    _inherit = ['mail.thread']

    def _get_active_lang(self):
        return self.env['res.lang'].get_installed()

    def _get_default_access_token(self):
        return uuid.uuid4().hex

    name = fields.Char("Template Name", required=True)
    model_id = fields.Many2one(
        "ir.model",
        string = "Model",
        required = True,
        ondelete = "cascade",
        tracking = True
    )
    model_name = fields.Char(related = "model_id.model")
    domain = fields.Char("Domain")
    sort_keys = fields.Char("Sort Keys")
    sort_reverse = fields.Boolean(string='Sort Reverse', default=False)
    field_ids = fields.One2many(
        comodel_name = "excel.template.field",
        inverse_name = "excel_template_id",
        string = "Fields"
    )
    lang = fields.Selection(
        _get_active_lang,
        string="Language",
        required = True
    )
    web_url = fields.Char("URL", compute = "_compute_template_web_url")
    access_token = fields.Char(
        "Access Token",
        default = lambda self: self._get_default_access_token(),
        readonly = True
    )
    company_id = fields.Many2one(
        "res.company",
        string = "Company"
    )
    state = fields.Selection(
        [("draft","Draft"),
        ("active","Active"),
        ("inactive","Inactive")],
        string = "State", default = "draft"
    )
    access_history_ids = fields.One2many(
        comodel_name = "excel.template.access.history",
        inverse_name = "excel_template_id",
        string = "Access History",
        readonly = True
    )
    user_id = fields.Many2one(
        "res.users",
        string = "Responsible",
        required = True,
        tracking = True
    )

    @api.onchange("model_id")
    def delete_template_fields_records(self):
        self.field_ids = [(6, 0, [])]

    def _compute_template_web_url(self):
        base_url = self.env["ir.config_parameter"].get_param("web.base.url")
        for rec in self:
            rec.web_url = f"{base_url}/get_excel_data/template/{str(rec.id)}/{rec.access_token}"

    def generate_access_token(self):
        for rec in self:
            rec.access_token = uuid.uuid4().hex

    _sql_constraints = [
        (
            'excel_template_name_uniq',
            'unique (name)',
            'Template name must be unique.',
        )
    ]

    def action_download_odc(self):
        self.ensure_one()
        if self.web_url and self.access_token:
            return {
                "type": "ir.actions.act_url",
                "target": "current",
                "url": f"/download_odc/template/{str(self.id)}"
            }

    def flush_access_history(self):
        self.ensure_one()
        if self.access_history_ids:
            self.access_history_ids = False
        return True

    def set_draft_state(self):
        for record in self:
            record.state = "draft"
        return True
    
    def set_active_state(self):
        for record in self:
            record.state = "active"
        return True
    
    def set_inactive_state(self):
        for record in self:
            record.state = "inactive"
        return True
