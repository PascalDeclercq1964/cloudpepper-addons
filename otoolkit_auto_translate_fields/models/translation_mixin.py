from odoo import models, fields, api, _


class TranslationMixin(models.AbstractModel):
    _name = 'otk.translation.mixin'
    _description = 'Translation Mixin'

    last_translation_date = fields.Datetime('Last Translation Date')

    def action_bulk_translate(self):
        return {
            'type': 'ir.actions.act_window',
            'name': _('Bulk translate'),
            'res_model': 'otk.translation.bulk.translate',
            'view_mode': 'form',
            'view_id': self.env.ref('otoolkit_auto_translate_fields.view_bulk_translate_wizard_form').id,
            'target': 'new',
        }

    @api.model
    def _get_view(self, view_id=None, view_type='search', **options):
        arch, view = super()._get_view(view_id, view_type, **options)
        if view_type == 'list':
            # Here we check if the action already exists
            model_name = self._name
            action_xml_id = 'bulk_translate_action_for_' + model_name.replace('.', '_')

            server_action = self.env.ref(f'otoolkit_auto_translate_fields.{action_xml_id}', raise_if_not_found=False)

            if not server_action:
                # Create the server action dynamically
                model = self.env['ir.model']._get(model_name)
                action_name = _('Bulk translate')
                server_action = self.env['ir.actions.server'].sudo().create({
                    'name': action_name,
                    'model_id': model.id,
                    'binding_model_id': model.id,
                    'binding_view_types': 'list',
                    'state': 'code',
                    'code': "action = env['%s'].action_bulk_translate()" % model_name,
                })
                self.env['ir.model.data'].sudo().create({
                    'name': action_xml_id,
                    'model': 'ir.actions.server',
                    'module': "otoolkit_auto_translate_fields",
                    'res_id': server_action.id,
                    'noupdate': True,
                })
        return arch, view