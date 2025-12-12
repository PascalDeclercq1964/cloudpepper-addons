from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class TranslationConfig(models.Model):
    _name = 'otk.translation.config'
    _description = 'Translation Configuration'
    _rec_name = 'model_id'

    model_id = fields.Many2one(
        'ir.model',
        string="Model",
        required=True,
        ondelete='cascade',
        domain="[('transient', '=', False)]",
    )
    active = fields.Boolean(default=True)
    has_translatable_fields = fields.Boolean(
        compute='_compute_has_translatable_fields',
        store=True,
    )
    translatable_field_ids = fields.Many2many(
        'ir.model.fields',
        string="Translatable Fields",
        compute='_compute_has_translatable_fields',
        store=True,
    )
    server_action_id = fields.Many2one(
        'ir.actions.server',
        string="Server Action",
        readonly=True,
        ondelete='set null',
    )

    @api.constrains('model_id')
    def _check_unique_model_id(self):
        for record in self:
            if record.model_id:
                if self.search([('model_id', '=', record.model_id.id), ('id', '!=', record.id)]):
                    raise ValidationError(_("A configuration already exists for this model."))

    @api.depends('model_id')
    def _compute_has_translatable_fields(self):
        for record in self:
            if record.model_id:
                translatable_fields = self.env['ir.model.fields'].search([
                    ('model_id', '=', record.model_id.id),
                    ('translate', '=', True),
                    ('related', '=', False),
                    ('store', '=', True),
                ])
                record.translatable_field_ids = translatable_fields
                record.has_translatable_fields = bool(translatable_fields)
            else:
                record.translatable_field_ids = False
                record.has_translatable_fields = False

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        records._create_server_actions()
        return records

    def write(self, vals):
        model_changed = 'model_id' in vals
        result = super().write(vals)
        if 'active' in vals or model_changed:
            self._update_server_actions(model_changed=model_changed)
        return result

    def unlink(self):
        self.server_action_id.unlink()
        return super().unlink()

    def _create_server_actions(self):
        """Create server actions for each configuration."""
        for record in self:
            if not record.server_action_id and record.model_id:
                record._create_single_server_action()

    def _create_single_server_action(self):
        """Create a single server action for this configuration."""
        self.ensure_one()
        if not self.model_id:
            return

        action_name = _('Bulk translate')
        server_action = self.env['ir.actions.server'].sudo().create({
            'name': action_name,
            'model_id': self.model_id.id,
            'binding_model_id': self.model_id.id,
            'binding_view_types': 'list',
            'state': 'code',
            'code': "action = env['otk.translation.config'].action_bulk_translate_generic()",
        })

        # Create external ID for the server action
        action_xml_id = 'bulk_translate_config_action_for_' + self.model_id.model.replace('.', '_')
        existing_data = self.env['ir.model.data'].sudo().search([
            ('module', '=', 'otoolkit_auto_translate_fields'),
            ('name', '=', action_xml_id),
        ])
        if existing_data:
            existing_data.unlink()

        self.env['ir.model.data'].sudo().create({
            'name': action_xml_id,
            'model': 'ir.actions.server',
            'module': 'otoolkit_auto_translate_fields',
            'res_id': server_action.id,
            'noupdate': True,
        })

        self.server_action_id = server_action

    def _update_server_actions(self, model_changed=False):
        """Update server actions when configuration changes."""
        for record in self:
            # If model changed, delete old action and create new one
            if model_changed and record.server_action_id:
                record.server_action_id.unlink()
                record.server_action_id = False

            if record.active and not record.server_action_id:
                record._create_single_server_action()
            elif not record.active and record.server_action_id:
                record.server_action_id.unlink()
                record.server_action_id = False

    @api.model
    def action_bulk_translate_generic(self):
        """Generic action to open bulk translate wizard - called from server actions."""
        active_model = self.env.context.get('active_model')
        if not active_model:
            return {'type': 'ir.actions.act_window_close'}

        return {
            'type': 'ir.actions.act_window',
            'name': _('Bulk translate'),
            'res_model': 'otk.translation.bulk.translate',
            'view_mode': 'form',
            'view_id': self.env.ref('otoolkit_auto_translate_fields.view_bulk_translate_wizard_form').id,
            'target': 'new',
        }

    def action_enable_all_translatable_models(self):
        """Enable bulk translation for all models that have translatable fields."""
        # Find all models with translatable fields
        translatable_models = self.env['ir.model.fields'].search([
            ('translate', '=', True),
            ('related', '=', False),
            ('store', '=', True),
        ]).mapped('model_id')

        # Filter out transient models and already configured models
        existing_model_ids = self.search([]).mapped('model_id.id')
        models_to_add = translatable_models.filtered(
            lambda m: m.id not in existing_model_ids and not m.transient
        )

        # Create configurations
        vals_list = [{'model_id': model.id} for model in models_to_add]
        created = self.create(vals_list)

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Bulk Translation Enabled'),
                'message': _('%d models have been configured for bulk translation.') % len(created),
                'type': 'success',
                'sticky': False,
            }
        }

    def action_view_translatable_fields(self):
        """View the translatable fields for this model."""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Translatable Fields'),
            'res_model': 'ir.model.fields',
            'view_mode': 'list,form',
            'domain': [('id', 'in', self.translatable_field_ids.ids)],
            'target': 'current',
        }
