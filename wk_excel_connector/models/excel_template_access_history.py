# -*- coding: utf-8 -*-
##########################################################################
#
#   Copyright (c) 2015-Present Webkul Software Pvt. Ltd. (<https://webkul.com/>)
#   See LICENSE file for full copyright and licensing details.
#   License URL : <https://store.webkul.com/license.html/>
#
##########################################################################

import math
import logging
from odoo import models, fields

_logger = logging.getLogger(__name__)

class ExcelTemplateAccessHistory(models.Model):
    _name = "excel.template.access.history"
    _description = "Excel Template Access History"
    _order = "last_use_date desc"

    def _compute_frequency(self):
        for rec in self:
            if rec.last_use_date and rec.no_of_use:
                dt = rec.last_use_date - rec.create_date
                frequency = math.ceil(dt.total_seconds()/rec.no_of_use)

                if frequency < 60:
                    rec.frequency = str(frequency) + " sec"
                elif frequency >= 60 and frequency < 3600:
                    minutes = frequency // 60
                    rec.frequency = str(minutes) + " min"
                else:
                    hour = frequency // 3600
                    frequency %= 3600
                    minute = frequency // 60
                    rec.frequency = str(hour) + "hr " + str(minute) + "min"

    excel_template_id = fields.Many2one(
        "excel.template",
        string = "Excel Template"
    )
    ip = fields.Char("IP Address", required=True)
    last_use_date = fields.Datetime("Last Used Date")
    no_of_use = fields.Integer("No of Times Used")
    frequency = fields.Char(
        "Frequency",
        compute = "_compute_frequency"
    )

    _sql_constraints = [
        (
            'excel_template_access_history_ip_uniq',
            'unique (excel_template_id, ip)',
            'IP Address must be unique per excel template',
        )
    ]
