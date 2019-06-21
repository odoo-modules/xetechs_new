import json
import odoo.http as http
from odoo.http import request
from odoo.addons.web.controllers.main import ExcelExport


class ExcelExportView(ExcelExport):
    def __getattribute__(self, name):
        if name == 'fmt':
            raise AttributeError()
        return super(ExcelExportView, self).__getattribute__(name)


    @http.route('/web/export/xls_view', type='http', auth='user')
    def export_xls_view(self, data, token):
        data = json.loads(data)
        table_header = data.get('headers', [])
        rows = data.get('rows', [])
        res_model = data.get('model', [])
        return request.make_response(
            self.from_data(table_header, rows),
            headers=[
                ('Content-Disposition', 'attachment; filename="%s"'
                 % self.filename(res_model)),
                ('Content-Type', self.content_type)
            ],
            cookies={'fileToken': token}
        )
