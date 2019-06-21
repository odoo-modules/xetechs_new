# -*- coding: utf-8 -*-

from odoo import api, fields, models, _


class IrListviewColumns(models.Model):
    _name = "ir.listview.columns"
    _description = "Listview Columns"

    view_id = fields.Many2one('ir.ui.view', string='View')
    list_columns = fields.Char(string='List Columns')
    user_id = fields.Many2one('res.users', string='User')