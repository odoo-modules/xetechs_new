# -*- coding: utf-8 -*-
#################################################################################
# Author      : Acespritech Solutions Pvt. Ltd. (<www.acespritech.com>)
# Copyright(c): 2012-Present Acespritech Solutions Pvt. Ltd.
# All Rights Reserved.
#
# This program is copyright property of the author mentioned above.
# You can`t redistribute it and/or modify it.
#
#################################################################################

from odoo import models, fields, api, _
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from odoo.exceptions import Warning
from lxml import etree
from odoo.osv.orm import setup_modifiers


class sales_target(models.Model):
    _name = 'sales.target'
    _inherit = ['mail.thread']
    _description = "Sales Target"

    @api.model
    def fields_view_get(self, view_id=None, view_type='form', toolbar=False, submenu=False):
        res = super(sales_target, self).fields_view_get(view_id=view_id, view_type=view_type, toolbar=toolbar,
                                                        submenu=submenu)
        if view_type == 'form':
            if not self.env.user.has_group('base.group_erp_manager'):
                doc = etree.XML(res['arch'])
                if doc.xpath("//field[@name='target_lines']"):
                    node = doc.xpath("//field[@name='target_lines']")[0]
                    node.set('readonly', '1')
                    setup_modifiers(node, res['fields']['target_lines'])
                res['arch'] = etree.tostring(doc)
        return res

    @api.multi
    def generate_target_period(self):
        target_line_obj = self.env['sales.target.line']
        if self.env.context.get('ctx_generate_target_call'):
            self.target_lines = False
        if self.date_start > self.date_end:
            raise Warning(_('End date must be greater than Start date.!'))
        if self.date_start < datetime.today().date():#.strftime('%Y-%m-01')
            raise Warning(_('You cannot set the target of Previous months.'))
        if self.target_period == 'Monthly':
            interval = 1
        elif self.target_period == 'Quarterly':
            interval = 3
        elif self.target_period == 'Semi-annually':
            interval = 6
        elif self.target_period == 'Yearly':
            interval = 12
#         dstart = datetime.strptime(self.date_start, '%Y-%m-%d')
        dstart = self.date_start
        while dstart <= self.date_end:#.strftime('%Y-%m-%d')
            dend = dstart + relativedelta(months=interval, days=-1)
            if dend > self.date_end:#.strftime('%Y-%m-%d')
                dend = self.date_end
            self.check_time_interval(dstart, dend, interval)
            if self.env.context.get('ctx_generate_target_call'):
                target_line_obj.create({'start_date': dstart.strftime('%Y-%m-%d'),
                                        'end_date': dend.strftime('%Y-%m-%d'),
                                        'target_id': self.id})
            dstart = dstart + relativedelta(months=interval)

    @api.multi
    def check_time_interval(self, dstart, dend, interval):
        # this method is check the date range in interval or not.
        if (relativedelta(dend + timedelta(days=1), dstart).years < 1) and interval == 12:
            raise Warning(_('Please select the date range, which has atleast %s month(s) interval period.') % interval)
        if (relativedelta(dend + timedelta(days=1), dstart).months < interval) and interval != 12:
            raise Warning(_('Please select the date range, which has atleast %s month(s) interval period.') % interval)
        return True

    @api.multi
    def set_to_draft(self):
        self.write({'state': 'draft'})

    @api.one
    def _check_target_status(self):
        # this method is for when all state of lines set to closed at that time the main target set to closed.
        for line in self.target_lines:
            if line.target_state == 'cancel':
                continue
            if fields.Date.from_string(line.end_date) < datetime.today().date():
                line.write({'target_state': 'closed'})
            else:
                line.write({'target_state': 'open'})
        if self.target_lines and all([line.target_state != 'open' for line in self.target_lines]):
            self.write({'state': 'closed'})
            self.check_lines_state = True

    user_id = fields.Many2one('res.users', string="Sales Person")
    date_start = fields.Date(string="Start Date")
    date_end = fields.Date(string="End Date")
    target_period = fields.Selection([('Monthly', 'Monthly'),
                                      ('Quarterly', 'Quarterly'),
                                      ('Semi-annually', 'Semi-annually'),
                                      ('Yearly', 'Yearly')], string="Target Period", default="Monthly")
    target_lines = fields.One2many('sales.target.line', 'target_id', string="Target Lines", copy=False)
    state = fields.Selection([('draft', 'Draft'), ('confirmed', 'Confirmed'),
                              ('cancel', 'Cancelled'), ('closed', 'Closed')],
                             string="State", copy=False, default="draft", track_visibility='onchange')
    name = fields.Char(string="", readonly=True)
    check_lines_state = fields.Boolean(string="Check Target", compute="_check_target_status")

    @api.model
    def create(self, vals):
        res = super(sales_target, self).create(vals)
        if res:
            res.write({'name': self.env['ir.sequence'].next_by_code('sales.target.number')})
            self.message_post(body=_('Hello %s, you have new sales target: %s') % (res.user_id.name, res.name),
                              partner_ids=[res.user_id.partner_id.id])
        return res

    @api.multi
    def write(self, vals):
        if vals.get('date_start') or vals.get('date_end') or vals.get('target_period') or vals.get('user_id'):
            for target in self:
                if any([line.target_state == 'closed' for line in target.target_lines]):
                    raise Warning(_('You cannot change the Start Date, End Date or Target Period.'))
        return super(sales_target, self).write(vals)

    @api.multi
    def target_confirmed(self):
        if not self.target_lines:
            raise Warning(_('Please generate sales target lines.!'))
        if (self.date_start != self.target_lines[0].start_date) or (self.date_end != self.target_lines[-1:].end_date):
            raise Warning(_(
                'Please generate the new target lines.'))  # for when target date is changed, and lines date remains old date.
        if any([line.target_amount <= 0 for line in self.target_lines]):
            raise Warning(_('Target amount must be greater than 0.'))
        self.generate_target_period()
        self._check_user_target_exist()
        self.write({'state': 'confirmed'})
        self.message_post(body=_('Hello %s, your target %s is confirmed from %s to %s') % (
        self.user_id.name, self.name, self.date_start, self.date_end),
                          partner_ids=[self.user_id.partner_id.id])
        if self.user_id.email:
            mail_message = """<p>Hello %s,<br/>
                                    You have new sales target <b>%s</b> from date %s to %s.<br/>
                                    Here below the details of your target.
                                  </p>
                                  <table border=1 width=400><tr>
                                            <th style='text-align:center'>Start of Target</th>
                                            <th style='text-align:center'>End of Target</th>
                                            <th style='text-align:center'>Target Amount</th>
                                         </tr>
                            """ % (self.user_id.name, self.name, self.date_start, self.date_end)
            for line in self.target_lines:
                if self.env.user.company_id.currency_id.position == 'before':
                    amount = self.env.user.company_id.currency_id.symbol or '' + " " + str(line.target_amount)
                else:
                    amount = str(line.target_amount) + " " + self.env.user.company_id.currency_id.symbol or ''
                mail_message += """<tr>
                                            <td style='text-align:center'>%s</td>
                                            <td style='text-align:center'>%s</td>
                                            <td style='text-align:center'>%s</td>
                                       </tr>
                                    """ % (line.start_date, line.end_date, amount)
            mail_message += "</table>"
            self.env['mail.mail'].create({'subject': 'Sales Target Details',
                                          'body_html': mail_message,
                                          'email_to': self.user_id.email,
                                          'email_from': self.env.user.company_id.email}).send()

    @api.multi
    def unlink(self):
        if any([tid.state in ['confirmed', 'closed'] for tid in self]):
            raise Warning(_('You cannot delete a target which is Confirmed or Closed.'))
        return super(sales_target, self).unlink()

    @api.multi
    def target_cancel(self):
        if any([line.target_state == 'closed' for line in self.target_lines]):
            raise Warning(_('You cannot cancel this target, because here some target lines are closed.'))
        for line in self.target_lines:
            if fields.Date.from_string(line.end_date) < datetime.today().date():
                raise Warning(
                    _('You cannot cancel this target, because here some target lines times already passed out.'))
        self.write({'state': 'cancel'})
        self.message_post(body=_('Hello %s, your target %s is cancelled.') % (self.user_id.name, self.name),
                          partner_ids=[self.user_id.partner_id.id])

    @api.multi
    def _check_user_target_exist(self):
        line_obj = self.env['sales.target.line']
        for target in self:
            tlineids = line_obj.search([('target_id.user_id', '=', target.user_id.id),
                                        ('target_id.state', '=', 'confirmed'),
                                        ('target_id', '<>', target.id)])
            for cur_target in target.target_lines:
                for other_target in tlineids:
                    if (other_target.start_date <= cur_target.start_date <= other_target.end_date) or \
                            (other_target.start_date <= cur_target.end_date <= other_target.end_date) or \
                            (cur_target.start_date <= other_target.start_date <= cur_target.end_date) or \
                            (cur_target.start_date <= other_target.end_date <= cur_target.end_date):
                        raise Warning(_('Target is already exist for the user %s') % (target.user_id.name))

    @api.multi
    def commission_graph(self):
        comm_ids = self.env['sales.commission'].search(['|', ('cons_id', '=', self.user_id.partner_id.id),
                                                        ('user_id', '=', self.user_id.id),
                                                        ('commission_date', '>=', str(self.date_start)),
                                                        ('commission_date', '<=', str(self.date_end))])
        if comm_ids:
            return {
                'type': 'ir.actions.act_window',
                'name': _('Sales Commission Graph'),
                'res_model': 'sales.commission',
                'view_type': 'form',
                'view_mode': 'graph',
                'domain': [('id', 'in', [each.id for each in comm_ids])],
            }
        else:
            raise Warning("No commission lines found.")


class sales_target_line(models.Model):
    _description = 'Sale Target Line'
    _name = 'sales.target.line'
    _order = 'start_date'

    @api.multi
    def _get_amount(self):
        comm_obj = self.env['sales.commission']
        for line in self:
            comm_ids = comm_obj.search([('user_id', '=', line.target_id.user_id.id),
                                        ('commission_date', '>=', line.start_date),
                                        ('commission_date', '<=', line.end_date),
                                        ('state', '!=', 'cancel')])
            line.commission_amount = sum([c.amount for c in comm_ids if c.state == 'paid'])

    target_id = fields.Many2one('sales.target', string="Target", ondelete="cascade")
    start_date = fields.Date(string="Start of Target")
    end_date = fields.Date(string="End of Target")
    target_amount = fields.Float(string="Target Amount")
    commission_amount = fields.Float(string="Commission Amount", compute="_get_amount")
    target_state = fields.Selection([('open', 'open'),
                                     ('closed', 'closed'),
                                     ('cancel', 'cancel')], string="State", default="open")

    @api.multi
    def state_cancel(self):
        for line in self:
            line.target_state = 'cancel'
            line.write({'target_state': 'cancel'})

    @api.multi
    def state_open(self):
        if fields.Date.from_string(self.end_date) < datetime.today().date():
            raise Warning(
                _('Selected target line time period is already passed out, so cannot reset this target line.'))
        self.write({'target_state': 'open'})