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
from datetime import datetime
from odoo.exceptions import Warning


class AccountConfiguration(models.TransientModel):
    _inherit = 'res.config.settings'

    @api.model
    def get_values(self):
        res = super(AccountConfiguration, self).get_values()
        IrDefault = self.env['ir.default'].sudo()
        res.update({
            'sales_person_commission_account_id': IrDefault.get('res.config.settings', "sales_person_commission_account_id", company_id=self.env.user.company_id.id) or False,
            'distributor_commission_account_id': IrDefault.get('res.config.settings', "distributor_commission_account_id", company_id=self.env.user.company_id.id) or False,
            'consultant_commission_account_id': IrDefault.get('res.config.settings', "consultant_commission_account_id", company_id=self.env.user.company_id.id) or False})
        return res

    @api.multi
    def set_values(self):
        res = super(AccountConfiguration, self).set_values()
        IrDefault = self.env['ir.default'].sudo()
        IrDefault.set('res.config.settings', "sales_person_commission_account_id", self.sales_person_commission_account_id.id, company_id=self.env.user.company_id.id)
        IrDefault.set('res.config.settings', "distributor_commission_account_id", self.distributor_commission_account_id.id, company_id=self.env.user.company_id.id)
        IrDefault.set('res.config.settings', "consultant_commission_account_id", self.consultant_commission_account_id.id, company_id=self.env.user.company_id.id)

    sales_person_commission_account_id = fields.Many2one('account.account', string="Sale Person Account", company_dependent=True)
    distributor_commission_account_id = fields.Many2one('account.account', string="Distributor Account", company_dependent=True)
    consultant_commission_account_id = fields.Many2one('account.account', string="Consultant Account", company_dependent=True)


class SaleAdvancePaymentInv(models.TransientModel):
    _inherit = "sale.advance.payment.inv"

    @api.multi
    def _create_invoice(self, order, so_line, amount):
        res = super(SaleAdvancePaymentInv, self)._create_invoice(order, so_line, amount)
        if res:
            res.update({'commission_calc': self.env[self._context.get('active_model')].browse(
                self._context.get('active_id')).commission_calc or '', 'commission_role_ids': self.env[self._context.get('active_model')].browse(
                self._context.get('active_id')).commission_role_ids or '', 'consultant_ids': self.env[self._context.get('active_model')].browse(
                self._context.get('active_id')).consultant_ids or ''})
        return res


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    def job_related_users(self, jobid):
        if jobid:
            empids = self.env['hr.employee'].search([('user_id', '!=', False), ('job_id', '=', jobid.id)])
            return [emp.user_id.id for emp in empids]
        return False

    @api.multi
    def action_invoice_cancel(self):
        res = super(AccountInvoice, self).action_invoice_cancel()
        comm_obj = self.env['sales.commission']
        for invoice in self:
            if invoice.commission_invoice:
                comm_ids = comm_obj.search([('invoice_id', '=', invoice.id), ('state', 'not in', ['cancel', 'paid'])])
                comm_ids.write({'state': 'draft', 'invoice_id': False})
        return res

    @api.multi
    def action_invoice_draft(self):
        res = super(AccountInvoice, self).action_invoice_draft()
        for invoice in self:
            if invoice.commission_invoice:
                for line in invoice.invoice_line_ids.filtered(lambda l: l.sale_commission_id):
                    if line.sale_commission_id.invoice_id:
                        raise Warning(_(
                            'Invoice cannot set as a Draft, because related commission lines assign to %s Invoice.') % (
                                      line.sale_commission_id.invoice_id.number or 'another'))
                    else:
                        if line.sale_commission_id.state == 'cancel':
                            raise Warning(
                                _('Invoice cannot set as a Draft, because %s commission line is Cancelled.') % (
                                line.sale_commission_id.name))
                        line.sale_commission_id.write({'state': 'invoiced', 'invoice_id': invoice.id})
        return res

    @api.multi
    def calculation_method(self, sale_id, inc_amont ,role_id, member_lst, details_lst):
        emp_id = self.env['hr.employee'].search([('user_id', '=', self.user_id.id)], limit=1)
        for role in self.commission_role_ids.filtered(lambda r: r.name == role_id.name):
            if self.commission_calc == 'product':
                for invline in self.invoice_line_ids:
                    if role.name == 'Sales Person':
                        for lineid in invline.product_id.product_comm_ids:
                            lines = {'user_id': self.user_id.id, 'job_id': emp_id.job_id.id,
                                     'commission_type': 'sales_person', 'user_sales_amount': 0.00}
                            details = {'name': invline.product_id.display_name,
                                       'person': self.user_id.partner_id.id,
                                       'role': role.id, 'type': lineid.compute_price_type,
                                       'commission': lineid.commission}
                            if (lineid.user_ids and self.user_id.id in [user.id for user in lineid.user_ids]) or \
                                    (lineid.job_id and not lineid.user_ids and self.user_id.id in self.job_related_users(lineid.job_id)):
                                lines['commission'] = invline.price_subtotal * lineid.commission / 100 if lineid.compute_price_type == 'per' else lineid.commission * invline.quantity
                                lines['user_sales_amount'] += invline.price_subtotal
                                member_lst.append(lines)
                                details['commission_amount'] = lines['commission']
                                details_lst.append(details)
                                break
                    elif role.name == 'Consultant':
                        for consultant in self.consultant_ids.filtered(lambda line: line.is_consultant):
                            for lineid in invline.product_id.product_cons_comm_ids:
                                if consultant.id == lineid.partner_id.id:
                                    member_lst.append({'partner_id': consultant.id, 'commission': invline.price_subtotal * lineid.commission / 100 if lineid.compute_price_type == 'per' else lineid.commission * invline.quantity,
                                                       'commission_type': 'consultant'})
                                    details_lst.append(
                                        {'name': invline.product_id.display_name, 'person': consultant.id,
                                         'role': role.id, 'type': lineid.compute_price_type,
                                         'commission': lineid.commission,
                                         'commission_amount': invline.price_subtotal * lineid.commission / 100 if lineid.compute_price_type == 'per' else lineid.commission * invline.quantity})
                                    break
                    elif role.name == 'Distributor' and self.partner_id and self.partner_id.is_distributor:
                        for lineid in invline.product_id.product_dist_comm_ids.filtered(lambda line: line.partner_id.id == self.partner_id.id):
                            member_lst.append({'partner_id': self.partner_id.id, 'commission': invline.price_subtotal * lineid.commission / 100 if lineid.compute_price_type == 'per' else lineid.commission * invline.quantity,
                                               'commission_type': 'distributor'})
                            details_lst.append(
                                {'name': invline.product_id.display_name, 'person': self.partner_id.id,
                                 'role': role.id, 'type': lineid.compute_price_type,
                                 'commission': lineid.commission,
                                 'commission_amount': invline.price_subtotal * lineid.commission / 100 if lineid.compute_price_type == 'per' else lineid.commission * invline.quantity})
                            break
            elif self.commission_calc == 'product_categ':
                for invline in self.invoice_line_ids:
                    if role.name == 'Sales Person':
                        for lineid in invline.product_id.categ_id.prod_categ_comm_ids:
                            lines = {'user_id': self.user_id.id, 'job_id': emp_id.job_id.id,
                                     'commission_type': 'sales_person','user_sales_amount': 0.00}
                            details = {'name': invline.product_id.categ_id.display_name, 'person': self.user_id.partner_id.id, 'role': role.id, 'type': lineid.compute_price_type, 'commission': lineid.commission}
                            if (lineid.user_ids and self.user_id.id in [user.id for user in lineid.user_ids]) or \
                                    (lineid.job_id and not lineid.user_ids and self.user_id.id in self.job_related_users(lineid.job_id)):
                                lines['commission'] = invline.price_subtotal * lineid.commission / 100 if lineid.compute_price_type == 'per' else lineid.commission * invline.quantity
                                lines['user_sales_amount'] += invline.price_subtotal
                                member_lst.append(lines)
                                details['commission_amount'] = lines['commission']
                                details_lst.append(details)
                                break
                    elif role.name == 'Consultant':
                        for consultant in self.consultant_ids.filtered(lambda line: line.is_consultant):
                            for lineid in invline.product_id.categ_id.prod_categ_cons_comm_ids:
                                if consultant.id == lineid.partner_id.id:
                                    member_lst.append({'partner_id': consultant.id, 'commission': invline.price_subtotal * lineid.commission / 100 if lineid.compute_price_type == 'per' else lineid.commission * invline.quantity,
                                                       'commission_type': 'consultant'})
                                    details_lst.append({'name': invline.product_id.categ_id.display_name,
                                                        'person': consultant.id,
                                                        'role': role.id, 'type': lineid.compute_price_type,
                                                        'commission': lineid.commission,
                                                        'commission_amount': invline.price_subtotal * lineid.commission / 100 if lineid.compute_price_type == 'per' else lineid.commission * invline.quantity})
                                    break
                    elif role.name == 'Distributor' and self.partner_id and self.partner_id.is_distributor:
                        for lineid in invline.product_id.categ_id.prod_categ_dist_comm_ids.filtered(lambda line: line.partner_id.id == self.partner_id.id):
                            member_lst.append({'partner_id': self.partner_id.id, 'commission': invline.price_subtotal * lineid.commission / 100 if lineid.compute_price_type == 'per' else lineid.commission * invline.quantity,
                                               'commission_type': 'distributor'})
                            details_lst.append({'name': invline.product_id.categ_id.display_name,
                                                'person': self.partner_id.id,
                                                'role': role.id, 'type': lineid.compute_price_type,
                                                'commission': lineid.commission,
                                                'commission_amount': invline.price_subtotal * lineid.commission / 100 if lineid.compute_price_type == 'per' else lineid.commission * lineid.commission * invline.quantity})
                            break
            elif self.commission_calc == 'customer' and self.partner_id:
                if role.name == 'Sales Person':
                    for lineid in self.partner_id.comm_ids:
                        lines = {'user_id': self.user_id.id, 'job_id': emp_id.job_id.id, 'commission_type': 'sales_person'}
                        details = {'name': self.partner_id.name, 'person': self.user_id.partner_id.id, 'role': role.id, 'type': lineid.compute_price_type, 'commission': lineid.commission}
                        if (lineid.user_ids and self.user_id.id in [user.id for user in lineid.user_ids]) or \
                                (lineid.job_id and not lineid.user_ids and self.user_id.id in self.job_related_users(lineid.job_id)):
                            if inc_amont == 'with_tax':
                                lines['commission'] = self.amount_total * lineid.commission / 100 if lineid.compute_price_type == 'per' else (lineid.commission * self.amount_total) / sale_id.amount_total
                                lines['user_sales_amount'] = self.amount_total
                            elif inc_amont == 'without_tax':
                                lines['commission'] = self.amount_untaxed * lineid.commission / 100 if lineid.compute_price_type == 'per' else (lineid.commission * self.amount_untaxed) / sale_id.amount_untaxed
                                lines['user_sales_amount'] = self.amount_untaxed
                            member_lst.append(lines)
                            details['commission_amount'] = lines['commission']
                            details_lst.append(details)
                            break
                elif role.name == 'Consultant':
                    for consultant in self.consultant_ids.filtered(lambda line: line.is_consultant):
                        for lineid in self.partner_id.consultant_comm_ids:
                            if consultant.id == lineid.partner_id.id:
                                lines = {'partner_id': consultant.id, 'commission_type': 'consultant'}
                                if inc_amont == 'with_tax':
                                    lines['commission'] = self.amount_total * lineid.commission / 100 if lineid.compute_price_type == 'per' else (lineid.commission * self.amount_total) / sale_id.amount_total
                                elif inc_amont == 'without_tax':
                                    lines['commission'] = self.amount_untaxed * lineid.commission / 100 if lineid.compute_price_type == 'per' else (lineid.commission * self.amount_untaxed) / sale_id.amount_untaxed
                                member_lst.append(lines)
                                details_lst.append(
                                    {'name': self.partner_id.name, 'person': consultant.id, 'role': role.id,
                                     'type': lineid.compute_price_type, 'commission': lineid.commission,
                                     'commission_amount': lines['commission']})
                                break
                elif role.name == 'Distributor' and self.partner_id and self.partner_id.is_distributor:
                    for lineid in self.partner_id.distributor_comm_ids.filtered(lambda line: line.partner_id.id == self.partner_id.id):
                        lines = {'partner_id': self.partner_id.id, 'commission_type': 'distributor'}
                        if inc_amont == 'with_tax':
                            lines['commission'] = self.amount_total * lineid.commission / 100 if lineid.compute_price_type == 'per' else (lineid.commission * self.amount_total) / sale_id.amount_total
                        elif inc_amont == 'without_tax':
                            lines['commission'] = self.amount_untaxed * lineid.commission / 100 if lineid.compute_price_type == 'per' else (lineid.commission * self.amount_untaxed) / sale_id.amount_untaxed
                        member_lst.append(lines)
                        details_lst.append(
                            {'name': self.partner_id.name, 'person': self.partner_id.id, 'role': role.id,
                             'type': lineid.compute_price_type, 'commission': lineid.commission,
                             'commission_amount': lines['commission']})
                        break
            elif self.commission_calc == 'sale_team' and self.team_id:
                if role.name == 'Sales Person':
                    for lineid in self.team_id.sale_team_comm_ids:
                        lines = {'user_id': self.user_id.id, 'job_id': emp_id.job_id.id, 'commission_type': 'sales_person'}
                        details = {'name': self.team_id.display_name, 'person': self.user_id.partner_id.id, 'role': role.id, 'type': lineid.compute_price_type, 'commission': lineid.commission}
                        if (lineid.user_ids and self.user_id.id in [user.id for user in lineid.user_ids]) or \
                                (lineid.job_id and not lineid.user_ids and self.user_id.id in self.job_related_users(lineid.job_id)):
                            if inc_amont == 'with_tax':
                                lines['commission'] = self.amount_total * lineid.commission / 100 if lineid.compute_price_type == 'per' else (lineid.commission * self.amount_total) / sale_id.amount_total
                                lines['user_sales_amount'] = self.amount_total
                            elif inc_amont == 'without_tax':
                                lines['commission'] = self.amount_untaxed * lineid.commission / 100 if lineid.compute_price_type == 'per' else (lineid.commission * self.amount_untaxed) / sale_id.amount_untaxed
                                lines['user_sales_amount'] = self.amount_untaxed
                            member_lst.append(lines)
                            details['commission_amount'] = lines['commission']
                            details_lst.append(details)
                            break
                elif role.name == 'Consultant':
                    for consultant in self.consultant_ids.filtered(lambda line: line.is_consultant):
                        for lineid in self.team_id.sale_team_cons_comm_ids:
                            if consultant.id == lineid.partner_id.id:
                                lines = {'partner_id': consultant.id, 'commission_type': 'consultant'}
                                if inc_amont == 'with_tax':
                                    lines['commission'] = self.amount_total * lineid.commission / 100 if lineid.compute_price_type == 'per' else (lineid.commission * self.amount_total) / sale_id.amount_total
                                elif inc_amont == 'without_tax':
                                    lines['commission'] = self.amount_untaxed * lineid.commission / 100 if lineid.compute_price_type == 'per' else (lineid.commission * self.amount_untaxed) / sale_id.amount_untaxed
                                member_lst.append(lines)
                                details_lst.append(
                                    {'name': self.team_id.display_name, 'person': consultant.id,
                                     'role': role.id, 'type': lineid.compute_price_type,
                                     'commission': lineid.commission,
                                     'commission_amount': lines['commission']})
                                break
                elif role.name == 'Distributor' and self.partner_id and self.partner_id.is_distributor:
                    for lineid in self.team_id.sale_team_dist_comm_ids.filtered(lambda line: line.partner_id.id == self.partner_id.id):
                        lines = {'partner_id': self.partner_id.id, 'commission_type': 'distributor'}
                        if inc_amont == 'with_tax':
                            lines['commission'] = self.amount_total * lineid.commission / 100 if lineid.compute_price_type == 'per' else (lineid.commission * self.amount_total) / sale_id.amount_total
                        elif inc_amont == 'without_tax':
                            lines['commission'] = self.amount_untaxed * lineid.commission / 100 if lineid.compute_price_type == 'per' else (lineid.commission * self.amount_untaxed) / sale_id.amount_untaxed
                        member_lst.append(lines)
                        details_lst.append({'name': self.team_id.display_name, 'person': self.partner_id.id,
                                            'role': role.id, 'type': lineid.compute_price_type,
                                            'commission': lineid.commission,
                                            'commission_amount': lines['commission']})
                        break

    @api.multi
    def invoice_validate(self):
        res = super(AccountInvoice, self).invoice_validate()
        ir_config_obj = self.env['ir.config_parameter']
        sale_comm_inc_amount = ir_config_obj.sudo().get_param('aspl_sales_commission_target_ee.commission_included_amount') if ir_config_obj.sudo().get_param('aspl_sales_commission_target_ee.commission_included_amount') else 'without_tax'
        dist_comm_inc_amount = ir_config_obj.sudo().get_param('aspl_sales_commission_target_ee.dist_commission_included_amount') if ir_config_obj.sudo().get_param('aspl_sales_commission_target_ee.dist_commission_included_amount') else 'without_tax'
        cons_comm_inc_amount = ir_config_obj.sudo().get_param('aspl_sales_commission_target_ee.cons_commission_included_amount') if ir_config_obj.sudo().get_param('aspl_sales_commission_target_ee.cons_commission_included_amount') else 'without_tax'
        commission_pay_on = ir_config_obj.sudo().get_param('aspl_sales_commission_target_ee.commission_pay_on')
        commission_pay_by = ir_config_obj.sudo().get_param('aspl_sales_commission_target_ee.commission_pay_by')
        cons_commission_pay_on = ir_config_obj.sudo().get_param('aspl_sales_commission_target_ee.cons_commission_pay_on')
        cons_commission_pay_by = ir_config_obj.sudo().get_param('aspl_sales_commission_target_ee.cons_commission_pay_by')
        dist_commission_pay_on = ir_config_obj.sudo().get_param('aspl_sales_commission_target_ee.dist_commission_pay_on')
        dist_commission_pay_by = ir_config_obj.sudo().get_param('aspl_sales_commission_target_ee.dist_commission_pay_by')
        sale_obj = self.env['sale.order']
        if self.commission_calc:
            emp_id = self.env['hr.employee'].search([('user_id', '=', self.user_id.id)], limit=1)
            sale_id = False
            for invoice in self:
                sale_id = sale_obj.search([('invoice_ids', 'in', [invoice.id])], limit=1)
            if sale_id:
                member_lst = []
                details_lst = []
                for role in self.commission_role_ids:
                    if role.name == 'Sales Person' and commission_pay_on == 'invoice_validate':
                        self.calculation_method(sale_id, sale_comm_inc_amount, role, member_lst, details_lst)
                    elif role.name == 'Consultant' and cons_commission_pay_on == 'invoice_validate':
                        self.calculation_method(sale_id, cons_comm_inc_amount, role, member_lst, details_lst)
                    elif role.name == 'Distributor' and dist_commission_pay_on == 'invoice_validate':
                        self.calculation_method(sale_id, dist_comm_inc_amount, role, member_lst, details_lst)
                userby = {}
                for member in member_lst:
                    if 'user_id' in member:
                        key = "user_" + str(member['user_id'])
                        if key in userby:
                            userby[key]['commission'] += member['commission']
                            userby[key]['user_sales_amount'] += member['user_sales_amount']
                        else:
                            userby.update({key: member})
                    if 'partner_id' in member:
                        key = "partner_" + str(member['partner_id'])
                        if key in userby:
                            userby[key]['commission'] += member['commission']
                        else:
                            userby.update({key: member})
                member_lst = []
                for user in userby:
                    member_lst.append((0, 0, userby[user]))
                self.sale_order_comm_ids = member_lst
                self.details_ids = False
                new_lst = []
                for detail in details_lst:
                    new_lst.append((0, 0, detail))
                self.update({
                    'details_ids': new_lst
                })

        if commission_pay_on == 'invoice_validate':
            for invoice in self:
                sale_id = sale_obj.search([('invoice_ids', 'in', [invoice.id])], limit=1)
                if sale_id:
                    sale_id.order_calculate_commission_cons_dist(ptype='sales_person', commission_pay_by=commission_pay_by, invoice_id=invoice)

        if cons_commission_pay_on == 'invoice_validate':
            for invoice in self:
                sale_id = sale_obj.search([('invoice_ids', 'in', [invoice.id])], limit=1)
                if sale_id:
                    sale_id.order_calculate_commission_cons_dist(ptype='consultant', commission_pay_by=cons_commission_pay_by, invoice_id=invoice)

        if dist_commission_pay_on == 'invoice_validate':
            for invoice in self:
                sale_id = sale_obj.search([('invoice_ids', 'in', [invoice.id])], limit=1)
                if sale_id:
                    sale_id.order_calculate_commission_cons_dist(ptype='distributor', commission_pay_by=dist_commission_pay_by, invoice_id=invoice)
        return res

    commission_invoice = fields.Boolean(string="Commission Invoice", copy=False)
    sale_order_comm_ids = fields.One2many('sales.order.commission', 'invoice_id', string="Sale Order Commission",
                                          store=True, readonly=True)
    commission_calc = fields.Selection([('sale_team', 'Sales Team'), ('customer', 'Customer'),
                                        ('product_categ', 'Product Category'),
                                        ('product', 'Product')], string="Commission Calculation", copy=False,
                                       readonly=True)
    commission_role_ids = fields.Many2many('sales.commission.role', string="Commission Role(s)", copy=False,
                                       readonly=True)
    consultant_ids = fields.Many2many('res.partner', string="Consultants", copy=False, readonly=True)
    details_ids = fields.One2many('commission.calculation.details', 'so_invoice_id', string="Details")


class AccountInvoiceLine(models.Model):
    _inherit = 'account.invoice.line'

    sale_commission_id = fields.Many2one('sales.commission', string="Sale Commission", readonly=True)


class AccountPayment(models.Model):
    _inherit = 'account.payment'

    @api.multi
    def post(self):
        super(AccountPayment, self).post()
        comm_obj = self.env['sales.commission']
        ir_config_obj = self.env['ir.config_parameter']
        sale_obj = self.env['sale.order']
        sale_comm_inc_amount = ir_config_obj.sudo().get_param('aspl_sales_commission_target_ee.commission_included_amount') if ir_config_obj.sudo().get_param('aspl_sales_commission_target_ee.commission_included_amount') else 'without_tax'
        dist_comm_inc_amount = ir_config_obj.sudo().get_param('aspl_sales_commission_target_ee.dist_commission_included_amount') if ir_config_obj.sudo().get_param('aspl_sales_commission_target_ee.dist_commission_included_amount') else 'without_tax'
        cons_comm_inc_amount = ir_config_obj.sudo().get_param('aspl_sales_commission_target_ee.cons_commission_included_amount') if ir_config_obj.sudo().get_param('aspl_sales_commission_target_ee.cons_commission_included_amount') else 'without_tax'
        commission_pay_on = ir_config_obj.sudo().get_param('aspl_sales_commission_target_ee.commission_pay_on')
        commission_pay_by = ir_config_obj.sudo().get_param('aspl_sales_commission_target_ee.commission_pay_by')
        cons_commission_pay_on = ir_config_obj.sudo().get_param('aspl_sales_commission_target_ee.cons_commission_pay_on')
        cons_commission_pay_by = ir_config_obj.sudo().get_param('aspl_sales_commission_target_ee.cons_commission_pay_by')
        dist_commission_pay_on = ir_config_obj.sudo().get_param('aspl_sales_commission_target_ee.dist_commission_pay_on')
        dist_commission_pay_by = ir_config_obj.sudo().get_param('aspl_sales_commission_target_ee.dist_commission_pay_by')
        for rec in self:
            for invoice in rec.invoice_ids:

                if invoice.commission_invoice and invoice.state == 'paid':
                    sale_commission = comm_obj.search([('invoice_id', '=', invoice.id)])
                    sale_commission.write({'state': 'paid', 'when_paid': datetime.now()})

                elif not invoice.commission_invoice and invoice.state == 'paid':
                    member_lst = []
                    details_lst = []
                    emp_id = self.env['hr.employee'].search([('user_id', '=', invoice.user_id.id)], limit=1)
                    sale_id = sale_obj.search([('invoice_ids', 'in', [invoice.id])], limit=1)
                    if sale_id:
                        for role in invoice.commission_role_ids:
                            if role.name == 'Sales Person' and commission_pay_on == 'invoice_pay':
                                invoice.calculation_method(sale_id, sale_comm_inc_amount, role, member_lst, details_lst)
                            elif role.name == 'Consultant' and cons_commission_pay_on == 'invoice_pay':
                                invoice.calculation_method(sale_id, cons_comm_inc_amount, role, member_lst, details_lst)
                            elif role.name == 'Distributor' and dist_commission_pay_on == 'invoice_pay':
                                invoice.calculation_method(sale_id, dist_comm_inc_amount, role, member_lst, details_lst)

                        userby = {}
                        for member in member_lst:
                            if 'user_id' in member:
                                key = "user_" + str(member['user_id'])
                                if key in userby:
                                    userby[key]['commission'] += member['commission']
                                    userby[key]['user_sales_amount'] += member['user_sales_amount']
                                else:
                                    userby.update({key: member})
                            if 'partner_id' in member:
                                key = "partner_" + str(member['partner_id'])
                                if key in userby:
                                    userby[key]['commission'] += member['commission']
                                else:
                                    userby.update({key: member})
                        member_lst = []
                        for user in userby:
                            member_lst.append((0, 0, userby[user]))

                        invoice.sale_order_comm_ids = member_lst
                        invoice.details_ids = False
                        new_lst = []
                        for detail in details_lst:
                            new_lst.append((0, 0, detail))
                        invoice.update({
                            'details_ids': new_lst
                        })

                    if commission_pay_on == 'invoice_pay':
                        sale_id = sale_obj.search([('invoice_ids', 'in', [invoice.id])], limit=1)
                        if sale_id:
                            if all([inv.state == 'paid' for inv in sale_id.invoice_ids]) and sale_id.invoice_status != 'to invoice':
                                sale_id.order_calculate_commission_cons_dist(ptype='sales_person', commission_pay_by=commission_pay_by, invoice_id=invoice)

                    if cons_commission_pay_on == 'invoice_pay':
                        sale_id = sale_obj.search([('invoice_ids', 'in', [invoice.id])], limit=1)
                        if sale_id:
                            if all([inv.state == 'paid' for inv in sale_id.invoice_ids]) and sale_id.invoice_status != 'to invoice':
                                sale_id.order_calculate_commission_cons_dist(ptype='consultant', commission_pay_by=cons_commission_pay_by, invoice_id=invoice)

                    if dist_commission_pay_on == 'invoice_pay':
                        sale_id = sale_obj.search([('invoice_ids', 'in', [invoice.id])], limit=1)
                        if sale_id:
                            if all([inv.state == 'paid' for inv in sale_id.invoice_ids]) and sale_id.invoice_status != 'to invoice':
                                sale_id.order_calculate_commission_cons_dist(ptype='distributor', commission_pay_by=dist_commission_pay_by, invoice_id=invoice)


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
