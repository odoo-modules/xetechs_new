# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
import datetime
import json


class KsDashboardNinjaBoard(models.Model):
    _name = 'ks_dashboard_ninja.board'

    name = fields.Char(string="Dashboard Name", required=True, size=35)
    ks_dashboard_items_ids = fields.One2many('ks_dashboard_ninja.item', 'ks_dashboard_ninja_board_id',
                                             string='Dashboard Items')
    ks_dashboard_menu_name = fields.Char(string="Menu Name")
    ks_dashboard_top_menu_id = fields.Many2one('ir.ui.menu', domain="[('parent_id','=',False)]",
                                               string="Show Under Menu")
    ks_dashboard_client_action_id = fields.Many2one('ir.actions.client')
    ks_dashboard_menu_id = fields.Many2one('ir.ui.menu')
    ks_dashboard_state = fields.Char()
    ks_dashboard_active = fields.Boolean(string="Active", default=True)
    ks_dashboard_group_access = fields.Many2many('res.groups', string="Group Access")

    # DateFilter Fields
    ks_dashboard_start_date = fields.Datetime()
    ks_dashboard_end_date = fields.Datetime()
    ks_date_filter_selection = fields.Selection([
        ('l_none', 'None'),
        ('l_day', 'Today'),
        ('l_week', 'Last 7 days'),
        ('l_month', 'Last 30 days'),
        ('l_quarter', 'Last 90 days'),
        ('l_year', 'Last 365 days'),
        ('l_custom', 'Custom Filter'),
    ], default='l_none')

    ks_gridstack_config = fields.Char('Item Configurations')
    ks_dashboard_default_template = fields.Many2one('ks_dashboard_ninja.board_template', default=lambda self:self.env.ref('ks_dashboard_ninja.ks_blank',False), string="Dashboard Template", required=True)

    ks_set_interval = fields.Selection([
        (15000, '15 Seconds'),
        (30000, '30 Seconds'),
        (45000, '45 Seconds'),
        (60000, '1 minute'),
        (120000, '2 minute'),
        (300000, '5 minute'),
        (600000, '10 minute'),
    ],string="Update Interval")

    @api.model
    def create(self, vals):
        record = super(KsDashboardNinjaBoard, self).create(vals)
        if 'ks_dashboard_top_menu_id' in vals and 'ks_dashboard_menu_name' in vals:
            action_id = {
                'name': vals['ks_dashboard_menu_name'] + " Action",
                'res_model': 'ks_dashboard_ninja.board',
                'tag': 'ks_dashboard_ninja',
                'params': {'ks_dashboard_id': record.id},
            }
            record.ks_dashboard_client_action_id = self.env['ir.actions.client'].sudo().create(action_id)

            if 'ks_dashboard_active' in vals:
                is_active = vals['ks_dashboard_active']

            record.ks_dashboard_menu_id = self.env['ir.ui.menu'].sudo().create({
                'name': vals['ks_dashboard_menu_name'],
                'active': is_active,
                'parent_id': vals['ks_dashboard_top_menu_id'],
                'action': "ir.actions.client," + str(record.ks_dashboard_client_action_id.id),
                'groups_id': vals['ks_dashboard_group_access'],
            })

        if record.ks_dashboard_default_template.ks_item_count:
            ks_gridstack_config = {}
            template_data = json.loads(record.ks_dashboard_default_template.ks_gridstack_config)
            for item_data in template_data:
                dashboard_item = self.env.ref(item_data['item_id']).copy({'ks_dashboard_ninja_board_id':record.id})
                ks_gridstack_config[dashboard_item.id] = item_data['data']
            record.ks_gridstack_config = json.dumps(ks_gridstack_config)
        return record

    @api.multi
    def write(self, vals):
        record = super(KsDashboardNinjaBoard, self).write(vals)
        for rec in self:
            if 'ks_dashboard_menu_name' in vals:
                if self.env.ref('ks_dashboard_ninja.ks_my_default_dashboard_board') and self.env.ref('ks_dashboard_ninja.ks_my_default_dashboard_board').sudo().id == rec.id:
                    if self.env.ref('ks_dashboard_ninja.board_menu_root',False):
                        self.env.ref('ks_dashboard_ninja.board_menu_root').sudo().name = vals['ks_dashboard_menu_name']
                else:
                    rec.ks_dashboard_menu_id.sudo().name = vals['ks_dashboard_menu_name']
            if 'ks_dashboard_group_access' in vals:
                if self.env.ref('ks_dashboard_ninja.ks_my_default_dashboard_board').id == rec.id:
                    if self.env.ref('ks_dashboard_ninja.board_menu_root',False):
                        self.env.ref('ks_dashboard_ninja.board_menu_root').groups_id = vals['ks_dashboard_group_access']
                else:
                    rec.ks_dashboard_menu_id.sudo().groups_id = vals['ks_dashboard_group_access']
            if 'ks_dashboard_active' in vals and rec.ks_dashboard_menu_id:
                rec.ks_dashboard_menu_id.sudo().active = vals['ks_dashboard_active']
        return record

    @api.multi
    def unlink(self):
        if self.env.ref('ks_dashboard_ninja.ks_my_default_dashboard_board').id in self.ids:
            raise ValidationError(_("Default Dashboard can't be deleted."))
        else:
            for rec in self:
                rec.ks_dashboard_client_action_id.sudo().unlink()
                rec.ks_dashboard_menu_id.sudo().unlink()
        res = super(KsDashboardNinjaBoard, self).unlink()
        return res

    @api.model
    def ks_fetch_dashboard_data(self, ks_dashboard_id):
        self.ks_set_date(ks_dashboard_id)
        has_group_ks_dashboard_manager = self.env.user.has_group('ks_dashboard_ninja.ks_dashboard_ninja_group_manager')
        dashboard_data = {
            'name': self.browse(ks_dashboard_id).name,
            'ks_dashboard_manager': has_group_ks_dashboard_manager,
            'ks_dashboard_list': self.search_read([], ['id', 'name']),
            'ks_dashboard_start_date': self.browse(ks_dashboard_id).ks_dashboard_start_date,
            'ks_dashboard_end_date': self.browse(ks_dashboard_id).ks_dashboard_end_date,
            'ks_date_filter_selection': self.browse(ks_dashboard_id).ks_date_filter_selection,
            'ks_gridstack_config': self.browse(ks_dashboard_id).ks_gridstack_config,
            'ks_set_interval': self.browse(ks_dashboard_id).ks_set_interval,
        }

        if len(self.browse(ks_dashboard_id).ks_dashboard_items_ids) < 1:
            dashboard_data['ks_item_data'] = False
        else:
            items = {}
            for rec in self.browse(ks_dashboard_id).ks_dashboard_items_ids:
                item = self.ks_fetch_item_data(rec)
                items[item['id']]=item
            dashboard_data['ks_item_data'] = items

        return dashboard_data

    # fetching Item info (Divided to make function inherit easily)
    def ks_fetch_item_data(self, rec):
        item = {
            'name': rec.name if rec.name else rec.ks_model_id.name if rec.ks_model_id else "Name",
            'color': rec.ks_background_color,
            'font_color': rec.ks_font_color,
            'domain': rec.ks_domain,
            'icon': rec.ks_icon,
            'model_id': rec.ks_model_name,
            'count': rec.ks_record_count,
            'id': rec.id,
            'layout': rec.ks_layout,
            'ks_icon_select': rec.ks_icon_select,
            'ks_default_icon': rec.ks_default_icon,
            'ks_default_icon_color': rec.ks_default_icon_color,
            #Pro Fields
            'ks_dashboard_item_type': rec.ks_dashboard_item_type,
            'ks_chart_item_color': rec.ks_chart_item_color,
            'ks_chart_groupby_type': rec.ks_chart_groupby_type,
            'ks_chart_relation_groupby': rec.ks_chart_relation_groupby.name,
            'ks_chart_date_groupby': rec.ks_chart_date_groupby,
            'ks_record_field': rec.ks_record_field.name,
            'ks_chart_data': rec.ks_chart_data,
            'ks_list_view_data': rec.ks_list_view_data,
            'ks_chart_data_count_type': rec.ks_chart_data_count_type,
        }
        return item

    # Setting Dat field value on everytime it fetches dashboard item information.
    def ks_set_date(self, ks_dashboard_id):
        ks_date_filter_selection = self.browse(ks_dashboard_id).ks_date_filter_selection
        date_filter_options = {
            'l_none': False,
            'l_day': 0,
            'l_week': 7,
            'l_month': 30,
            'l_quarter': 90,
            'l_year': 365,
            'l_custom': False,
        }
        if ks_date_filter_selection in date_filter_options.keys() and ks_date_filter_selection not in ['l_custom',
                                                                                                       'l_none']:
            selected_end_date = fields.datetime.now().strftime("%Y-%m-%d 23:59:59")
            selected_start_date = (fields.datetime.now() - datetime.timedelta(
                days=date_filter_options[ks_date_filter_selection])).strftime("%Y-%m-%d 00:00:00")
            self.browse(ks_dashboard_id).write({'ks_dashboard_end_date': selected_end_date,
                                                'ks_dashboard_start_date': selected_start_date})

    @api.multi
    def load_previous_data(self):

        for rec in self:
            if rec.ks_dashboard_menu_id and rec.ks_dashboard_menu_id.action._table == 'ir_act_window':
                action_id = {
                    'name': rec['ks_dashboard_menu_name'] + " Action",
                    'res_model': 'ks_dashboard_ninja.board',
                    'tag': 'ks_dashboard_ninja',
                    'params': {'ks_dashboard_id': rec.id},
                }
                rec.ks_dashboard_client_action_id = self.env['ir.actions.client'].sudo().create(action_id)
                rec.ks_dashboard_menu_id.write(
                    {'action': "ir.actions.client," + str(rec.ks_dashboard_client_action_id.id)})


class KsDashboardNinjaTemplate(models.Model):
    _name = 'ks_dashboard_ninja.board_template'

    name = fields.Char()
    ks_gridstack_config = fields.Char()
    ks_item_count = fields.Integer()
