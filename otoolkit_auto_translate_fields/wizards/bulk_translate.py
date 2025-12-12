from odoo import fields, models, api


class BulkTranslate(models.TransientModel):
    _name = 'otk.translation.bulk.translate'
    _description = "Bulk translate Wizard"

    model_id = fields.Many2one('ir.model', string="Model", ondelete='cascade')
    base_language_id = fields.Many2one('res.lang', string="Base language", required=True, ondelete='cascade')
    target_language_ids = fields.Many2many('res.lang', string="Target languages", required=True, ondelete='cascade')
    field_ids = fields.Many2many(
        'ir.model.fields',
        string="Fields",
        domain="[('translate', '=', True), ('model_id', '=', model_id), ('related', '=', False), ('store', '=', True)]",
        required=True
    )

    @api.depends('model_id')
    def _compute_model_name(self):
        for record in self:
            record.model_name = record.model_id.model

    @api.model
    def default_get(self, fields_list):
        defaults = super().default_get(fields_list)
        active_model = self.env.context.get('active_model')
        if active_model:
            model = self.env['ir.model'].search([('model', '=', active_model)], limit=1)
            defaults['model_id'] = model.id
            defaults['base_language_id'] = self.env['res.lang'].search([('code', '=', self.env.user.lang)], limit=1)
            defaults['target_language_ids'] = self.env['res.lang'].search([('code', '!=', self.env.user.lang)])
        return defaults

    def action_translate(self):
        active_ids = self.env.context.get('active_ids')
        self.env['otk.translation.action'].sudo().create({
            'model_id': self.model_id.id,
            'base_language_id': self.base_language_id.id,
            'target_language_ids': self.target_language_ids.ids,
            'field_ids': self.field_ids.ids,
            'pending_record_ids': active_ids,
            'translation_count': len(active_ids),
        })