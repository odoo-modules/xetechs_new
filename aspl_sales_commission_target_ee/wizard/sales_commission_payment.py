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
from odoo.exceptions import Warning, ValidationError
from datetime import datetime
import base64


class SalesCommissionPayment(models.TransientModel):
    _description = 'Sale Commission Payment'
    _name = 'sales.commission.payment'

    @api.multi
    def generate_invoice(self):
        invoice_obj = self.env['account.invoice']
        scobj = self.env['sales.commission']
        invoice_id = False
        domain = [('state', '=', 'draft'), ('pay_by', '=', 'invoice'),
                  '|', ('invoice_id', '=', False), ('invoice_id.state', '=', 'cancel')]
        if self.start_date and self.end_date:
            if self.start_date > self.end_date:
                raise Warning(_('End Date should be greater than Start Date.'))
            domain.append(('commission_date', '>=', self.start_date))
            domain.append(('commission_date', '<=', self.end_date))
        else:
            domain.append(('commission_date', '<=', self.end_date or fields.Date.today()))
        if self.user_id:
            domain.append(('user_id', '=', self.user_id.id))
        if self.consultant_id:
            domain.append(('cons_id', '=', self.consultant_id.id))
        if self.distributor_id:
            domain.append(('cons_id', '=', self.distributor_id.id))
        if self.type:
            domain.append(('type', '=', self.type))
        commission_ids = self._context.get('commission_ids')
        if not commission_ids:
            commission_ids = self.env['sales.commission'].search(domain)
        journal_id = invoice_obj.with_context({'type': 'in_invoice', 'journal_type': 'purchase',
                                               'company_id': self.env.user.company_id.id})._default_journal()
        if not journal_id:
            raise Warning(_('Account Journal not found.'))

        IrDefault = self.env['ir.default'].sudo()
        if self.type == 'sales_person':
            partner_id = self.user_id.partner_id.id
            commission_account_id = IrDefault.get('res.config.settings', "sales_person_commission_account_id", company_id=self.env.user.company_id.id)
        elif self.type == 'consultant':
            partner_id = self.consultant_id.id
            commission_account_id = IrDefault.get('res.config.settings', "consultant_commission_account_id", company_id=self.env.user.company_id.id)
        elif self.type == 'distributor':
            partner_id = self.distributor_id.id
            commission_account_id = IrDefault.get('res.config.settings', "distributor_commission_account_id", company_id=self.env.user.company_id.id)
        if not commission_account_id:
            raise Warning(_('Commission Account is not Found. Please go to Accounting-> Configuration and set the Sales commission account.'))
        else:
            account_id = self.env['account.account'].search([('id', '=', commission_account_id)])
        if account_id:
            if self.type in ['consultant', 'distributor']:
                inv_line_data = []
                for commid in commission_ids:
                    inv_line_data.append((0, 0, {'account_id': account_id.id,
                                                 'name': commid.name + " Commission",
                                                 'quantity': 1,
                                                 'price_unit': commid.amount,
                                                 'sale_commission_id': commid.id
                                                 }))
                if inv_line_data:
                    invoice_vals = {'partner_id': partner_id,
                                    'company_id': self.env.user.company_id.id,
                                    'commission_invoice': True,
                                    'type': 'in_invoice',
                                    'journal_id': journal_id.id,
                                    'invoice_line_ids': inv_line_data,
                                    'origin': 'Commission Invoice',
                                    'date_due': datetime.today().date(),
                                    }
                    invoice_id = invoice_obj.search(
                        [('partner_id', '=', partner_id), ('state', '=', 'draft'),
                         ('type', '=', 'in_invoice'), ('commission_invoice', '=', True),
                         ('company_id', '=', self.env.user.company_id.id)])
                    if invoice_id:
                        invoice_id.write({'invoice_line_ids': inv_line_data, 'commission_invoice': True})
                    else:
                        invoice_id = invoice_obj.create(invoice_vals)
                        invoice_id._onchange_partner_id()
                    for commid in commission_ids:
                        commid.write({'invoice_id': invoice_id.id, 'state': 'invoiced'})
                if invoice_id:
                    view_id = self.env.ref("account.invoice_supplier_form")
                    return {
                            "name":"Commission Invoice",
                            "type":"ir.actions.act_window",
                            "view_id":view_id.id,
                            "view_type":"form",
                            "view_mode":"form",
                            "res_model":"account.invoice",
                            "res_id":invoice_id.id
                            }
                else:
                    raise Warning("No Invoice found or Generated.")
            elif self.type == 'sales_person':
                user_obj = self.env['res.users']
                user_dict = {}
                target_line_obj = self.env['sales.target.line']
                self.env['sales.target'].search([('state', '=', 'confirmed')])._check_target_status()
                for commline in commission_ids:
                    if not user_dict.get(commline.user_id.id):
                        user_dict.update({commline.user_id.id: {'target': {}, 'without_target': []}})
                    target_line_id = target_line_obj.search([('target_id.state', 'in', ['confirmed', 'closed']),
                                                             ('target_id.user_id', '=', commline.user_id.id),
                                                             ('start_date', '<=', commline.commission_date),
                                                             ('end_date', '>=', commline.commission_date)], order="id desc", limit=1)
                    if target_line_id:
                        if (target_line_id.target_state == 'open') or (target_line_id.start_date <= fields.Date.today() <= target_line_id.end_date):
                            continue
                        if target_line_id.target_state == 'cancel':
                            user_dict[commline.user_id.id]['without_target'].append(commline)
                        else:
                            if not user_dict[commline.user_id.id]['target'].get(target_line_id):
                                user_dict[commline.user_id.id]['target'].update({target_line_id: []})
                            user_dict[commline.user_id.id]['target'][target_line_id].append(commline)
                    else:
                        user_dict[commline.user_id.id]['without_target'].append(commline)

                for user, vals in user_dict.items():
                    commission_lines = []
                    userid = user_obj.browse(user)
                    inv_line_data = []
                    for commid in vals.get('without_target'):
                        inv_line_data.append((0, 0, {'account_id': account_id.id,
                                                     'name': commid.name + " Commission",
                                                     'quantity': 1,
                                                     'price_unit': commid.amount,
                                                     'sale_commission_id': commid.id}))
                        commission_lines.append(commid)
                    for t_lineid, comm_ids in vals.get('target').items():
                        if self.start_date and self.end_date:
                            cur_target_other_comm_ids = scobj.search(
                                [('state', '=', 'draft'), ('pay_by', '=', 'invoice'),
                                 '|', ('invoice_id', '=', False), ('invoice_id.state', '=', 'cancel'),
                                 ('user_id', '=', user),
                                 ('commission_date', '>=', t_lineid.start_date),
                                 ('commission_date', '<=', t_lineid.end_date)])
                            if len(cur_target_other_comm_ids) != len(comm_ids):
                                continue
                        total_sales_amount = sum([cid.user_sales_amount for cid in comm_ids])
                        if (total_sales_amount >= t_lineid.target_amount) or self.override_target:
                            for commid in comm_ids:
                                inv_line_data.append((0, 0, {'account_id': account_id.id,
                                                             'name': commid.name + " Commission",
                                                             'quantity': 1,
                                                             'price_unit': commid.amount,
                                                             'sale_commission_id': commid.id}))
                                commission_lines.append(commid)
                    if inv_line_data:
                        invoice_vals = {'partner_id': userid.partner_id.id,
                                        'company_id': self.env.user.company_id.id,
                                        'commission_invoice': True,
                                        'type': 'in_invoice',
                                        'journal_id': journal_id.id,
                                        'invoice_line_ids': inv_line_data,
                                        'origin': 'Commission Invoice',
                                        'date_due': datetime.today().date()}
                        invoice_id = invoice_obj.search([('partner_id', '=', userid.partner_id.id),
                                                         ('state', '=', 'draft'), ('type', '=', 'in_invoice'),
                                                         ('commission_invoice', '=', True),
                                                         ('company_id', '=', self.env.user.company_id.id)])
                        if invoice_id:
                            invoice_id.write({'invoice_line_ids': inv_line_data, 'commission_invoice': True})
                        else:
                            invoice_id = invoice_obj.create(invoice_vals)
                            invoice_id._onchange_partner_id()
                        for commid in commission_lines:
                            commid.write({'invoice_id': invoice_id.id, 'state': 'invoiced'})
                if invoice_id:
                    view_id = self.env.ref("account.invoice_supplier_form")
                    return {
                            "name":"Commission Invoice",
                            "type":"ir.actions.act_window",
                            "view_id":view_id.id,
                            "view_type":"form",
                            "view_mode":"form",
                            "res_model":"account.invoice",
                            "res_id":invoice_id.id
                            }
                else:
                   raise Warning("No Invoice found or Generated.")

    start_date = fields.Date(string='Start Date')
    end_date = fields.Date(string='End Date')
    type = fields.Selection([('sales_person', 'Sales Person'), ('consultant', 'Consultant'),
                             ('distributor', 'Distributor')], string="Type", default="sales_person")
    user_id = fields.Many2one('res.users', string="User")
    consultant_id = fields.Many2one('res.partner', string="Consultant", domain=[('is_consultant', '=', True)])
    distributor_id = fields.Many2one('res.partner', string="Distributor", domain=[('is_distributor', '=', True)])
    override_target = fields.Boolean(string='Override Target',
                                     help="If checked, then it will override user's Commission Target.")


class wizard_commission_summary(models.TransientModel):
    _description = 'Commission Summary Wizard'
    _name = 'wizard.commission.summary'

    start_date = fields.Date(string="Start Date")
    end_date = fields.Date(string="End Date")
    job_ids = fields.Many2many('hr.job', string="Job(s)")
    user_ids = fields.Many2many('res.users', string="User(s)")
    consultant_ids = fields.Many2many('res.partner', 'consultant_partner_rel', string="Consultant(s)", domain=[('is_consultant', '=', True)])
    distributor_ids = fields.Many2many('res.partner', 'distributor_partner_rel', string="Distributor(s)", domain=[('is_distributor', '=', True)])
    status = fields.Selection([('paid', 'Paid'), ('unpaid', 'Unpaid'),
                               ('cancel', 'Cancel'), ('all', 'All')], string="Status", default='paid', required=True)
    template_id = fields.Many2one('mail.template', string="Mail Template")
    mail_to = fields.Many2many('res.partner', string='Mail To')
    type = fields.Selection([('sales_person', 'Sales Person'), ('consultant', 'Consultant'),
                             ('distributor', 'Distributor'), ('all', 'All')], string="Type", default='sales_person')

    @api.onchange('job_ids')
    def onchange_job(self):
        res = {'value': {'user_ids': False}}
        if self.job_ids:
            job_lst = [job.id for job in self.job_ids]
            emp_ids = self.env['hr.employee'].search([('user_id', '!=', False), ('job_id', 'in', job_lst)])
            user_lst = list(set([emp.user_id.id for emp in emp_ids]))
            res.update({'domain': {'user_ids': [('id', 'in', user_lst)]}})
            if self.env.context.get('ctx_job_user_report_print'):
                return user_lst
        return res

    @api.multi
    def get_users_commission(self):
        result = {}
        user_ids = [user.id for user in self.user_ids or self.env['res.users'].search([])]
        consultant_ids = [user.id for user in self.consultant_ids or self.env['res.partner'].search([('is_consultant', '=', True)])]
        distributor_ids = [user.id for user in self.distributor_ids or self.env['res.partner'].search([('is_distributor', '=', True)])]
        if not self.user_ids and self.job_ids:
            user_ids = self.with_context({'ctx_job_user_report_print': True}).onchange_job()
        domain = [('type', '=', self.type)] if self.type != 'all' else []
        if self.type == 'sales_person':
            domain.append(('user_id', 'in', user_ids))
        elif self.type == 'consultant':
            domain.append(('cons_id', 'in', consultant_ids))
        elif self.type == 'distributor':
            domain.append(('cons_id', 'in', distributor_ids))
        if self.status in ['paid', 'cancel']:
            domain.append(('state', '=', self.status))
        elif self.status == 'unpaid':
            domain.append(('state', 'in', ['draft', 'invoiced']))
        if self.start_date and self.end_date:
            domain.append(('commission_date', '>=', str(self.start_date)))
            domain.append(('commission_date', '<=', str(self.end_date)))
        for commid in self.env['sales.commission'].search(domain, order="commission_date"):
            vals = {'name': commid.name,
                    'client': commid.client.name,
                    'state': commid.state,
                    'date': commid.commission_date,
                    'user_name': commid.user_id.name if commid.user_id.name else commid.cons_id.name,
                    'amount': commid.amount}
            key = 'sales_person_' + str(commid.user_id.id) if commid.type == 'sales_person' else 'cons_' + str(commid.cons_id.id)
            result[key].append(vals) if key in result else result.update({key: [vals]})
        if not result:
            raise Warning(_('Sales Commission Details not found.'))
        return result

    @api.multi
    def print_commission_report(self):
        if self.start_date > self.end_date:
            raise Warning(_('End Date should be greater than Start Date.'))
        datas = {
            'ids': self._ids,
            'model': 'wizard.commission.summary',
            'form': self.read()[0],
            'commission_details': self.get_users_commission()
        }
        return self.env.ref('aspl_sales_commission_target_ee.report_print_commission_summary').report_action(self, data=datas)

    @api.multi
    def send_commission_report(self):
        if self.start_date > self.end_date:
            raise Warning(_('End Date should be greater than Start Date.'))
        if self.mail_to and self.template_id:
            mail_obj = self.env['mail.mail']
            datas = {
                'ids': self._ids,
                'model': 'wizard.commission.summary',
                'form': self.read()[0],
                'commission_details': self.get_users_commission()
            }
            pdf_data = self.env.ref('aspl_sales_commission_target_ee.report_print_commission_summary').render_qweb_pdf(self, data=datas)
            if pdf_data:
                pdfvals = {'name': 'Commission Summary',
                           'db_datas': base64.b64encode(pdf_data[0]),
                           'datas': base64.b64encode(pdf_data[0]),
                           'datas_fname': 'Commission_Summary.pdf',
                           'res_model': 'sales.commission',
                           'type': 'binary'}
                pdf_create = self.env['ir.attachment'].create(pdfvals)
                values = {
                    'subject': 'Commission Summary',
                    'body_html': self.template_id.body_html,
                    'email_to': ','.join(each.email for each in self.mail_to),
                    'email_from': self.env.user.email,
                    'attachment_ids': [(6, 0, [pdf_create.id])]
                }
                msg_id = mail_obj.create(values)
                msg_id.send()
                return True
        elif not self.mail_to:
            raise Warning(_('Email id is not defined to send email. Please Enter Email id !'))
        elif not self.template_id:
            raise Warning(_('Please Select Email template !'))


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
