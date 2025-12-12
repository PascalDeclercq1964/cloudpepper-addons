import requests
from odoo import models, fields, api


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    otoolkit_api_key = fields.Char(
        string='Otoolkit API key',
        config_parameter='otoolkit_api_key',
        help='This API key allow you to communicate with the otoolkit api.',
    )

    otoolkit_api_token_count = fields.Integer(
        string='Token Count',
        compute='_compute_token_count',
        config_parameter='otoolkit_api_token_count',
        readonly=True,
        default=-100000000
    )

    def get_token_count(self, api_key):
        api_endpoint = self.env['ir.config_parameter'].sudo().get_param('otoolkit.api.endpoint')
        if not api_key:
            return -100000000
        headers = {
            'Odoo-Api-Key': api_key,
            'Content-Type': 'application/json'
        }
        url = f"{api_endpoint}/api/get-token-count/"
        try:
            response = requests.request("GET", url, headers=headers)
        except Exception:
            return -100000001

        if response.status_code == 200:
            return response.json()["token_count"]

        return -100000001

    @api.depends('otoolkit_api_key')
    def _compute_token_count(self):
        for record in self:
            api_key = record.otoolkit_api_key
            record.otoolkit_api_token_count = record.get_token_count(api_key)
            self.env['ir.config_parameter'].sudo().set_param('otoolkit_api_token_count', str(record.otoolkit_api_token_count))

    def refresh_token_count(self):
        self._compute_token_count()
