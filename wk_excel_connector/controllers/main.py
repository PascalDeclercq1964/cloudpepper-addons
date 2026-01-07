# -*- coding: utf-8 -*-
##########################################################################
#
#   Copyright (c) 2015-Present Webkul Software Pvt. Ltd. (<https://webkul.com/>)
#   See LICENSE file for full copyright and licensing details.
#   License URL : <https://store.webkul.com/license.html/>
#
##########################################################################

import logging
import io, csv
import ast
from odoo import http, fields
from odoo.http import request
from odoo.tools import pycompat, html_escape
from operator import itemgetter

_logger = logging.getLogger(__name__)

class WkExcelController(http.Controller):

    @http.route('/get_excel_data/template/<int:template_id>/<string:access_token>', type='http', auth='public', methods=["GET"])
    def get_excel_data(self, template_id, access_token):
        create = True
        template_domain = [('id','=',template_id),('access_token','=',access_token)]
        template = request.env['excel.template'].sudo().search(template_domain,limit=1)
        if not template:
            return "Template not found."
        if template.state != 'active':
            return "Template is not active."
        ip = request.httprequest.environ.get('REMOTE_ADDR')
        if template.access_history_ids:
            historyObj = template.access_history_ids.filtered(lambda h: h.ip == ip)
            if historyObj:
                create = False
                historyObj.last_use_date = fields.Datetime.now()
                historyObj.no_of_use += 1
        if create:
            request.env["excel.template.access.history"].with_user(template.user_id.id).create(
                {
                    "excel_template_id": template.id,
                    "ip": ip,
                    "last_use_date": fields.Datetime.now(),
                    "no_of_use": 1
                }
            )
        domain = []
        if template.domain:
            domain = ast.literal_eval(template.domain)
        field_keys, labels = self.get_field_labels(template)
        records = request.env[template.model_name].with_user(template.user_id.id).with_context(lang=template.lang).search(domain)
        if template.sort_keys:
            sort_keys = template.sort_keys
            data_sort_type = template.sort_reverse
            split_sort_keys = sort_keys.split(',')
            data = records.sorted(key=itemgetter(*split_sort_keys),reverse=bool(data_sort_type)).with_user(template.user_id.id).export_data(field_keys).get('datas', [])
        else:
            data = records.with_user(template.user_id.id).export_data(field_keys).get('datas', [])

        
        for i, rec in enumerate(data):
            image_urls = []
            c=0
            for j, item in enumerate(rec):
                if isinstance(item, bytes):
                    base_url = request.env['ir.config_parameter'].sudo().get_param('web.base.url')
                    local_url='{}/web/image/{}/{}/{}'.format(base_url, template.model_name,records.ids[i],field_keys[j])
                    image_urls.append(local_url)
              
                else:
                    image_urls.append(item)
            data[i] = image_urls
               
     
        file_name = f'{template.name}.csv'
      
        return request.make_response(
            self.get_csv_data(data, labels),
            headers=[
                ('Content-Type', 'text/csv;charset=utf8'),
                ('Content-Disposition', f'inline; filename="{file_name}"'),
            ])
    
def get_field_labels(self, template):
        field_keys, labels = [], []
        for field in template.field_ids:
            key = field.field_id.name
            
            # --- AANPASSING START ---
            
            # 1. Is het veld een Many2one relatie? (bv. partner_id)
            # Gebruik dan /.id (met een punt!) om de Database ID te krijgen i.p.v. de XML ID.
            if field.field_id.ttype == 'many2one':
                key += '/.id'
                
            # 2. Is het veld het hoof-ID van de regel zelf?
            # 'id' geeft standaard de XML-ID terug. '.id' geeft het getal.
            elif key == 'id':
                key = '.id'
                
            # --- AANPASSING EIND ---

            field_keys.insert(field.sequence, key)
            labels.insert(field.sequence, field.name)

        return field_keys, labels     
        
    def get_csv_data(self, data, labels):
      
        file = io.BytesIO()
        writer = pycompat.csv_writer(file, quoting=csv.QUOTE_NONNUMERIC)
        writer.writerow(labels)
        writer.writerows(data)
        return file.getvalue()

    @http.route('/download_odc/template/<int:template_id>', type='http', auth='user')
    def download_odc(self, template_id):
       
        template = request.env['excel.template'].browse(template_id)
        if not template:
            return "Template not found."
        data = f"""<!DOCTYPE html>
        <html>
            <head>
                <meta http-equiv="Content-Type" content="text/x-ms-odc; charset=utf-8"/>
                <meta name="ProgId" content="ODC.Database"/>
                <meta name="SourceType" content="OLEDB"/>
                <title>Query - {template.name}</title>
                <xml id="msodc">
                    <odc:OfficeDataConnection xmlns:odc="urn:schemas-microsoft-com:office:odc" xmlns="http://www.w3.org/TR/REC-html40">
                        <odc:PowerQueryConnection odc:Type="OLEDB">
                            <odc:ConnectionString>Provider=Microsoft.Mashup.OleDb.1;Data Source=$Workbook$;Location=&quot;{template.name}&quot;;</odc:ConnectionString>
                            <odc:CommandType>SQL</odc:CommandType>
                            <odc:CommandText>SELECT * FROM [{template.name}]</odc:CommandText>
                        </odc:PowerQueryConnection>
                        <odc:PowerQueryMashupData>
                            {html_escape(self._get_power_query_data(template))}
                        </odc:PowerQueryMashupData>
                    </odc:OfficeDataConnection>
                </xml>
            </head>
            <body></body>
        </html>
        """

        file_name = f'{template.name}.odc'
        
       
        return request.make_response(
            data,
            headers=[
                ('Content-Type', 'text/x-ms-odc;charset=utf8'),
                ('Content-Disposition', f'inline; filename="{file_name}"'),
            ])

    def _get_power_query_data(self, template):
        types = []
        for field in template.field_ids:
            typ = f'"{field.name}", type {self._get_field_type(field)}'
            types.append('{' + typ + '}')
        type_str = '{' + ','.join(types) + '}'
        lang = (template.lang or 'en_US').replace('_', '-')

        formula_list = [
            f'let url = "{template.web_url}",',
            'Source = Csv.Document(Web.Contents(url), [Delimiter=","]),',
            '#"Fixed Headers" = Table.PromoteHeaders(Source, [PromoteAllScalars=true]),',
            f'#"Converted Result" = Table.TransformColumnTypes(#"Fixed Headers", {type_str}, "{lang}")',
            'in #"Converted Result"'
        ]
        formula = '\n'.join(formula_list)

        return f"""<Mashup xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns="http://schemas.microsoft.com/DataMashup">
                <Client>EXCEL</Client>
                <SafeCombine>true</SafeCombine>
                <Items>
                    <Query Name="{template.name}">
                        <Formula><![CDATA[{formula}]]></Formula>
                        <IsParameterQuery xsi:nil="true"/>
                        <IsDirectQuery xsi:nil="true"/>
                    </Query>
                </Items>
            </Mashup>"""
    
    def _get_field_type(self, field):
        ttype = field.field_id.ttype
        if ttype in ('integer', 'float', 'monetary'):
            return 'number'
        if ttype == 'date':
            return 'date'
        if ttype == 'datetime':
            return 'datetime'
        return 'text'
