import json
import copy
import datetime

import requests
import time
from odoo import models, fields, api, _


class TranslationAction(models.Model):
    _name = 'otk.translation.action'
    _description = 'Translation Action'
    _rec_name = 'display_name'
    _order = 'id desc'

    display_name = fields.Char(string="Name", compute='_compute_display_name', store=True, readonly=True)

    model_id = fields.Many2one('ir.model', string="Model", ondelete='cascade', readonly=True)
    base_language_id = fields.Many2one('res.lang', string="Language", readonly=True)
    target_language_ids = fields.Many2many('res.lang', string="Target languages", required=True, ondelete='cascade',
                                           readonly=True)
    field_ids = fields.Many2many(
        'ir.model.fields',
        string="Fields to translate",
        domain="[('translate', '=', True), ('model_id', '=', model_id)]",
        readonly=True,
    )
    pending_record_ids = fields.Json(default=list, string="Pending translations", readonly=True)
    processing_record_ids = fields.Json(default=list, string="Processing translations", readonly=True)
    done_record_ids = fields.Json(default=list, string="Done translations", readonly=True)
    error_record_ids = fields.Json(default=list, string="Error translations", readonly=True)
    progress = fields.Float(store=True, string="Progress", compute="_compute_progress", readonly=True)
    translation_count = fields.Integer(readonly=True, string="Translation count")
    token_cost = fields.Integer(default=0, string="Token used", readonly=True)

    translation_ids = fields.One2many(
        comodel_name='otk.translation',
        inverse_name='action_id',
        string='Translations',
        readonly=True)

    status = fields.Selection(
        [('pending', 'Pending'), ('done', 'Done'), ('error', 'Error'), ('processing', 'Processing')],
        compute='_compute_status',
        string='Status',
        store=True
    )

    def translate_model(self, model, target_langs, record_id):
        api_key = self.env['ir.config_parameter'].sudo().get_param('otoolkit_api_key')
        api_endpoint = self.env['ir.config_parameter'].sudo().get_param('otoolkit.api.endpoint')
        if not api_key:
            return False, 0

        payload = json.dumps({
            "object": model,
            "target_langs": target_langs,
            "record_id": record_id,
            "odoo_user_id": self.env.user.id
        })

        headers = {
            'Odoo-Api-Key': api_key,
            'Content-Type': 'application/json'
        }
        url = f"{api_endpoint}/api/auto-translate-fields/v2/translate-model/"
        try:
            response = requests.request("POST", url, headers=headers, data=payload)
        except Exception:
            self.env["otk.translation"].create({
                'action_id': self.id,
                'cost': 0,
                'record_id': record_id,
                'status': 'error'
            })
            return False, 0
        if response.status_code != 200:
            self.env["otk.translation"].create({
                'action_id': self.id,
                'cost': 0,
                'record_id': record_id,
                'status': 'translation_error' if response.status_code != 401 else 'api_key_error',
                'translations': 'An error has occurred. You can restart the translation from the parent action.' if response.status_code != 401 else 'Your api key is invalid. Use a valid key and restart the translation from the parent action.',
            })
            pending = self.pending_record_ids if self.pending_record_ids else []
            error = self.error_record_ids if self.error_record_ids else []
            pending.remove(record_id)
            if record_id not in error:
                error.append(record_id)
            self.write({
                'pending_record_ids': pending,
                'error_record_ids': error,
            })
            return False, 0
        data = response.json()

        return data["task_id"]

    def cron_translate_action(self):
        max_time = 60
        max_record = 10
        max_iter = 10
        action = self.env['otk.translation.action'].sudo().search([('status', '=', 'pending')], order='id asc', limit=1)
        start = int(time.time())

        while action and max_iter > 0:
            can_restart = self.translate_action(action, max_record)
            if not can_restart:
                break
            action = self.env['otk.translation.action'].sudo().search([('status', '=', 'pending')], order='id asc',
                                                                      limit=1)
            if int(time.time()) - start > max_time:
                break

            max_iter -= 1

        self.cron_retrieve_tasks()

    def cron_retrieve_tasks(self):
        pending_translations = self.env["otk.translation"].sudo().search([('status', '=', 'pending')], order='id asc',
                                                                         limit=100)

        if len(pending_translations) == 0:
            return

        api_key = self.env['ir.config_parameter'].sudo().get_param('otoolkit_api_key')
        api_endpoint = self.env['ir.config_parameter'].sudo().get_param('otoolkit.api.endpoint')
        if not api_key:
            return

        payload = json.dumps({
            "task_ids": pending_translations.mapped('task_id'),
        })

        headers = {
            'Odoo-Api-Key': api_key,
            'Content-Type': 'application/json'
        }
        url = f"{api_endpoint}/api/tasks/"

        try:
            response = requests.request("POST", url, headers=headers, data=payload)
            tasks = response.json()["tasks"]
        except Exception as e:
            print(e)
            return

        task_map = {task["id"]: task for task in tasks}
        action_update = {}

        for translation in pending_translations:
            action_id = translation.action_id.id
            if action_id not in action_update:
                action_update[action_id] = {
                    'error': [],
                    'completed': [],
                    'action': translation.action_id,
                }

            related_task = task_map.get(translation.task_id)
            active_id = related_task['params']['record_id']

            if related_task:
                if related_task["status"] == "completed":
                    action_update[action_id]['completed'].append(active_id)
                    action = action_update[action_id]['action']
                    record = self.env[action.model_id.model].with_context(lang=action.base_language_id.code).browse(active_id)

                    translatable_object = related_task['params']['object']
                    target_langs = related_task['params']['target_langs']
                    translations = related_task['result']['translated_object']
                    cost = related_task['result']['cost']

                    previous_values = {}

                    for field in action.field_ids:
                        if not hasattr(record, field.name):
                            continue

                        base_value = translatable_object.get(field.name)
                        if base_value:
                            translate_column = f"{field.name}"

                            query = f"""
                                                    SELECT {translate_column}
                                                    FROM {self.env[action.model_id.model]._table}
                                                    WHERE id = %s
                                                """
                            self.env.cr.execute(query, (active_id,))
                            result = self.env.cr.fetchone()
                            translate = result[0] if result and result[0] else {}

                            translate[action.base_language_id.code] = base_value
                            previous_values[field.name] = copy.deepcopy(translate)

                            for lang in target_langs:
                                translate[lang] = translations[field.name][lang]

                            update_query = f"""
                                                            UPDATE {self.env[action.model_id.model]._table}
                                                            SET {translate_column} = %s
                                                            WHERE id = %s
                                                        """
                            self.env.cr.execute(update_query, (json.dumps(translate), active_id))

                    translation.write({
                        'cost': cost,
                        'status': 'success',
                        'translations': translations,
                        'initial_values': previous_values,
                    })
                    # Update last_translation_date only if the field exists on the model
                    # (for backward compatibility with models using the mixin)
                    if 'last_translation_date' in self.env[action.model_id.model]._fields:
                        record.write({
                            "last_translation_date": datetime.datetime.now(),
                        })
                elif related_task["status"] == "failed":
                    action_update[action_id]['error'].append(active_id)
                    translation.write({
                        'status': 'error',
                    })
        for key, value in action_update.items():
            action = value['action']
            processing = action.processing_record_ids if action.processing_record_ids else []
            error = action.error_record_ids if action.error_record_ids else []
            done = action.done_record_ids if action.done_record_ids else []

            for translation_id in value['completed']:
                processing.remove(translation_id)
                done.append(translation_id)

            for translation_id in value['error']:
                processing.remove(translation_id)
                error.append(translation_id)

            action.write({
                'processing_record_ids': processing,
                'error_record_ids': error,
                'done_record_ids': done,
            })

    def translate_action(self, action, max_record):
        active_ids = action.pending_record_ids[0:max_record]
        langs = action.target_language_ids
        target_langs = []
        for lang in langs:
            if lang.code != action.base_language_id.code:
                target_langs.append(lang.code)

        error_count = 0
        translations_to_create = []

        for active_id in active_ids:
            record = self.env[action.model_id.model].with_context(lang=action.base_language_id.code).browse(active_id)

            translatable_object = {}
            for field in action.field_ids:
                value = getattr(record, field.name)
                if value and value != "":
                    translatable_object[field.name] = getattr(record, field.name)

            task_id = action.translate_model(translatable_object, target_langs, active_id)

            if not task_id:
                error_count += 1
                continue

            translations_to_create.append({
                'action_id': action.id,
                'cost': 0,
                'record_id': active_id,
                'status': 'pending',
                'translations': {},
                'initial_values': {},
                'task_id': task_id
            })

            pending = action.pending_record_ids if action.pending_record_ids else []
            processing = action.processing_record_ids if action.processing_record_ids else []
            pending.remove(active_id)
            if active_id not in processing:
                processing.append(active_id)
            action.write({
                'pending_record_ids': pending,
                'processing_record_ids': processing,
            })

        self.env["otk.translation"].create(
            translations_to_create
        )

        return error_count != len(active_ids)

    def retry_error_translation(self):
        for record in self:
            pending = record.pending_record_ids if record.pending_record_ids else []
            error = record.error_record_ids if record.error_record_ids else []
            pending.extend(error)
            self.write({
                'pending_record_ids': pending,
                'error_record_ids': [],
            })

    @api.depends('pending_record_ids', 'done_record_ids')
    def _compute_progress(self):
        for record in self:
            if not record.done_record_ids:
                record.progress = 0.0
            elif not record.pending_record_ids and not record.processing_record_ids:
                record.progress = 100.0
            else:
                record.progress = len(record.done_record_ids) / record.translation_count * 100.0

    @api.depends('progress', 'error_record_ids')
    def _compute_status(self):
        for record in self:
            if record.error_record_ids and len(record.error_record_ids) > 0 and (
                    not record.pending_record_ids or len(record.pending_record_ids) == 0) and (
                    not record.processing_record_ids or len(record.processing_record_ids) == 0):
                record.status = 'error'
            else:
                record.status = 'done' if record.progress >= 100 else 'pending' if record.pending_record_ids and len(
                    record.pending_record_ids) > 0 else 'processing'

    @api.depends('model_id')
    def _compute_display_name(self):
        for record in self:
            record.display_name = "Action #" + str(record.id) + " - " + record.model_id.name


class Translation(models.Model):
    _name = 'otk.translation'
    _description = 'Translation object with the details of the translation, the cost...'
    _order = 'id desc'

    action_id = fields.Many2one('otk.translation.action', string="Linked action", ondelete='cascade', readonly=True)
    record_id = fields.Integer(string='Record id', readonly=True)
    model_id = fields.Many2one('ir.model', string='Model', readonly=True, related='action_id.model_id')

    cost = fields.Float(string="Token used", readonly=True)
    status = fields.Selection(
        [
            ('error', "Error"),
            ('translation_error', "Translation Error"),
            ('api_key_error', "Api Key Error"),
            ('success', "Success"),
            ('revert', "Revert"),
            ('pending', "Pending"),
        ],
        string="Status", readonly=True
    )
    translations = fields.Json(string='Translations', readonly=True)
    initial_values = fields.Json(string='Initial value', readonly=True)

    task_id = fields.Integer(string="Task ID", readonly=True)

    def revert_translation(self):
        for record in self:
            initial = record.initial_values
            for field in record.translations:
                query = f"""
                            SELECT {field} 
                            FROM {self.env[record.model_id.model]._table} 
                            WHERE id = %s
                        """
                self.env.cr.execute(query, (record.record_id,))
                result = self.env.cr.fetchone()
                translate = result[0] if result and result[0] else {}

                for lang in record.translations[field]:
                    initial_value = initial[field].get(lang)
                    if not initial_value:
                        initial_value = False
                    translate[lang] = initial_value

                update_query = f"""
                                    UPDATE {self.env[record.model_id.model]._table}
                                    SET {field} = %s
                                    WHERE id = %s
                                """
                self.env.cr.execute(update_query, (json.dumps(translate), record.record_id))

        record.status = 'revert'

    def open_record(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Linked record',
            'res_model': self.model_id.model,
            'res_id': self.record_id,
            'view_mode': 'form',
            'target': 'current',  # or 'new' to open in a popup
        }
