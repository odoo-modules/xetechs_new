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
from lxml import etree
from odoo.osv.orm import setup_modifiers


class SaleConfiguration(models.TransientModel):
    _inherit = 'res.config.settings'

    @api.model
    def get_values(self):
        res = super(SaleConfiguration, self).get_values()
        param_obj = self.env['ir.config_parameter']
        res.update({
            'commission_pay_on': param_obj.sudo().get_param('aspl_sales_commission_target_ee.commission_pay_on'),
            'commission_pay_by': param_obj.sudo().get_param('aspl_sales_commission_target_ee.commission_pay_by'),
            'commission_included_amount': param_obj.sudo().get_param('aspl_sales_commission_target_ee.commission_included_amount'),
            'dist_commission_pay_on': param_obj.sudo().get_param('aspl_sales_commission_target_ee.dist_commission_pay_on'),
            'dist_commission_pay_by': param_obj.sudo().get_param('aspl_sales_commission_target_ee.dist_commission_pay_by'),
            'dist_commission_included_amount': param_obj.sudo().get_param('aspl_sales_commission_target_ee.dist_commission_included_amount'),
            'cons_commission_pay_on': param_obj.sudo().get_param('aspl_sales_commission_target_ee.cons_commission_pay_on'),
            'cons_commission_pay_by': param_obj.sudo().get_param('aspl_sales_commission_target_ee.cons_commission_pay_by'),
            'cons_commission_included_amount': param_obj.sudo().get_param('aspl_sales_commission_target_ee.cons_commission_included_amount'),
        })
        return res

    @api.multi
    def set_values(self):
        res = super(SaleConfiguration, self).set_values()
        param_obj = self.env['ir.config_parameter']
        param_obj.sudo().set_param('aspl_sales_commission_target_ee.commission_pay_on',self.commission_pay_on)
        param_obj.sudo().set_param('aspl_sales_commission_target_ee.commission_pay_by', self.commission_pay_by)
        param_obj.sudo().set_param('aspl_sales_commission_target_ee.commission_included_amount', self.commission_included_amount)
        param_obj.sudo().set_param('aspl_sales_commission_target_ee.dist_commission_pay_on', self.dist_commission_pay_on)
        param_obj.sudo().set_param('aspl_sales_commission_target_ee.dist_commission_pay_by', self.dist_commission_pay_by)
        param_obj.sudo().set_param('aspl_sales_commission_target_ee.dist_commission_included_amount', self.dist_commission_included_amount)
        param_obj.sudo().set_param('aspl_sales_commission_target_ee.cons_commission_pay_on', self.cons_commission_pay_on)
        param_obj.sudo().set_param('aspl_sales_commission_target_ee.cons_commission_pay_by', self.cons_commission_pay_by)
        param_obj.sudo().set_param('aspl_sales_commission_target_ee.cons_commission_included_amount', self.cons_commission_included_amount)

    commission_pay_on = fields.Selection([('order_confirm', 'Sales Order Confirmation'),
                                          ('invoice_validate', 'Customer Invoice Validation'),
                                          ('invoice_pay', 'Customer Invoice Payment')], string="Sales Pay On")
    commission_pay_by = fields.Selection([('invoice', 'Invoice'), ('salary', 'Salary')], string="Sales Pay By")
    commission_included_amount = fields.Selection([('with_tax', 'With Tax'), ('without_tax', 'Without Tax')],
                                           string="Sales Included Amount", default='without_tax')
    dist_commission_pay_on = fields.Selection([('order_confirm', 'Sales Order Confirmation'),
                                          ('invoice_validate', 'Customer Invoice Validation'),
                                          ('invoice_pay', 'Customer Invoice Payment')], string="Distributor Pay On")
    dist_commission_pay_by = fields.Selection([('invoice', 'Invoice'), ('salary', 'Salary')], string="Distributor Pay By")
    dist_commission_included_amount = fields.Selection([('with_tax', 'With Tax'), ('without_tax', 'Without Tax')],
                                                  string="Distributor Included Amount", default='without_tax')
    cons_commission_pay_on = fields.Selection([('order_confirm', 'Sales Order Confirmation'),
                                          ('invoice_validate', 'Customer Invoice Validation'),
                                          ('invoice_pay', 'Customer Invoice Payment')], string="Consultant Pay On")
    cons_commission_pay_by = fields.Selection([('invoice', 'Invoice'), ('salary', 'Salary')], string="Consultatn Pay By")
    cons_commission_included_amount = fields.Selection([('with_tax', 'With Tax'), ('without_tax', 'Without Tax')],
                                                  string="Consultant Included Amount", default='without_tax')


class SalesOrderCommission(models.Model):
    _description = 'Sales Order Commission'
    _name = 'sales.order.commission'

    user_id = fields.Many2one('res.users', string="User")
    partner_id = fields.Many2one('res.partner', string="Consultant/Distributor")
    job_id = fields.Many2one('hr.job', string="Job Position")
    commission = fields.Float(string="Commission")
    order_id = fields.Many2one('sale.order', string="Order")
    commission_type = fields.Selection([('sales_person', 'Sales Person'), ('consultant', 'Consultant'),
                             ('distributor', 'Distributor')], string="Commission Type")
    invoice_id = fields.Many2one('account.invoice', string="Invoice")
    user_sales_amount = fields.Float(string="Sales Amount")

    @api.multi
    def commission_details(self):
        domain = [('role.name', 'ilike', self.commission_type)]
        if self.order_id and self.user_id:
            domain.append(('so_order_id', '=', self.order_id.id))
            domain.append(('person', '=', self.user_id.partner_id.id))
        if self.invoice_id and self.partner_id:
            domain.append(('so_invoice_id', '=', self.invoice_id.id))
            domain.append(('person', '=', self.partner_id.id))
        return {
            'type': 'ir.actions.act_window',
            'name': 'Commission Calculation Details',
            'res_model': 'commission.calculation.details',
            'view_type': 'form',
            'view_mode': 'tree',
            'target': 'current',
            'domain': domain,
        }


class SalesCommissionRole(models.Model):
    _description = 'Sale Commission Role'
    _name = 'sales.commission.role'

    name = fields.Char(string='Name')


class CommissionCalculationDetails(models.Model):
    _description = 'Commission Calc. Details'
    _name = 'commission.calculation.details'

    name = fields.Char(string="Source Name")
    person = fields.Many2one('res.partner', string="Person Name")
    role = fields.Many2one('sales.commission.role', string="Role")
    type = fields.Selection([('fix_price', 'Fix Price'), ('per', 'Percentage')], string="Type")
    commission = fields.Float(string="Commission")
    commission_amount = fields.Float(string="Commission Amount")
    so_order_id = fields.Many2one('sale.order', string="Sale Order", readonly=True)
    so_invoice_id = fields.Many2one('account.invoice', string="Account Invoice", readonly=True)


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    @api.multi
    def _prepare_invoice(self):
        self.ensure_one()
        res = super(SaleOrder, self)._prepare_invoice()
        if res:
            res.update({'commission_calc': self.commission_calc or '', 'commission_role_ids': [(6,0,([each.id for each in self.commission_role_ids]))] if self.commission_role_ids else '',
                        'consultant_ids': [(6,0,([each.id for each in self.consultant_ids]))] if self.consultant_ids else ''})
        return res

    def default_commission_role_id(self):
        return self.env['sales.commission.role'].search([('name', '=', 'Sales Person')])

    @api.multi
    def action_cancel(self):
        res = super(SaleOrder, self).action_cancel()
        comm_obj = self.env['sales.commission']
        for saleid in self:
            comm_obj.search([('state', '=', 'draft'), ('name', '=', saleid.name)]).write({'state': 'cancel'})
        return res

    @api.one
    def order_calculate_commission(self, ptype, commission_pay_by):
        comm_obj = self.env['sales.commission']
        for commline in self.sale_order_comm_ids.filtered(lambda l:l.commission_type == ptype):
            vals = {
                'name': self.name,
                'sale_id': self.id,
                'client': self.partner_id.id,
                'commission_date': datetime.today().date(),
                'amount': commline.commission,
                'pay_by': commission_pay_by or 'invoice',
                'user_sales_amount': commline.user_sales_amount,
                'type': commline.commission_type,
                'user_id': commline.user_id.id,
                'cons_id': commline.partner_id.id
            }
            if commline.user_id:
                comm_ids = comm_obj.search(
                    [('user_id', '=', commline.user_id.id), ('type', '=', commline.commission_type),
                     ('name', '=', self.name), ('state', '!=', 'cancel')])
            elif commline.partner_id:
                comm_ids = comm_obj.search(
                    [('cons_id', '=', commline.partner_id.id), ('type', '=', commline.commission_type),
                     ('name', '=', self.name), ('state', '!=', 'cancel')])
            total_paid_amount = sum(
                comm_ids.filtered(lambda cid: cid.state == 'paid' or cid.invoice_id).mapped('amount'))
            if total_paid_amount <= commline.commission:
                vals['amount'] = commline.commission - total_paid_amount
            total_sales_amount = sum(
                comm_ids.filtered(lambda cid: cid.state == 'paid' or cid.invoice_id).mapped('user_sales_amount'))
            if total_sales_amount <= commline.user_sales_amount:
                vals['user_sales_amount'] = commline.user_sales_amount - total_sales_amount
            comm_ids.filtered(lambda cid: cid.state == 'draft' and not cid.invoice_id).unlink()
            if vals['amount'] != 0.0:
                comm_obj.create(vals)

    @api.one
    def order_calculate_commission_cons_dist(self, ptype, commission_pay_by, invoice_id):
        comm_obj = self.env['sales.commission']
        for commline in invoice_id.sale_order_comm_ids.filtered(lambda l: l.commission_type == ptype):
            vals = {
                'name': self.name,
                'sale_id': self.id,
                'client': self.partner_id.id,
                'commission_date': datetime.today().date(),
                'amount': commline.commission,
                'pay_by': commission_pay_by or 'invoice',
                'user_sales_amount': commline.user_sales_amount,
                'type': commline.commission_type,
                'user_id': commline.user_id.id,
                'cons_id': commline.partner_id.id,
                'reference_invoice_id': invoice_id.id,
            }
            if commline.user_id:
                comm_ids = comm_obj.search(
                    [('user_id', '=', commline.user_id.id), ('type', '=', commline.commission_type),
                     ('name', '=', self.name), ('state', '!=', 'cancel'), ('reference_invoice_id', '=', invoice_id.id)])
            elif commline.partner_id:
                comm_ids = comm_obj.search(
                    [('cons_id', '=', commline.partner_id.id), ('type', '=', commline.commission_type),
                     ('name', '=', self.name), ('state', '!=', 'cancel'), ('reference_invoice_id', '=', invoice_id.id)])
            total_paid_amount = sum(
                comm_ids.filtered(lambda cid: cid.state == 'paid' or cid.invoice_id).mapped('amount'))
            if total_paid_amount <= commline.commission:
                vals['amount'] = commline.commission - total_paid_amount
            total_sales_amount = sum(
                comm_ids.filtered(lambda cid: cid.state == 'paid' or cid.invoice_id).mapped('user_sales_amount'))
            if total_sales_amount <= commline.user_sales_amount:
                vals['user_sales_amount'] = commline.user_sales_amount - total_sales_amount
            comm_ids.filtered(lambda cid: cid.state == 'draft' and not cid.invoice_id).unlink()
            if vals['amount'] != 0.0:
                comm_obj.create(vals)

    @api.multi
    def write(self, vals):
        res = super(SaleOrder, self).write(vals)
        ir_config_obj = self.env['ir.config_parameter']
        commission_pay_on = ir_config_obj.sudo().get_param('aspl_sales_commission_target_ee.commission_pay_on')
        commission_pay_by = ir_config_obj.sudo().get_param('aspl_sales_commission_target_ee.commission_pay_by')
        cons_commission_pay_on = ir_config_obj.sudo().get_param('aspl_sales_commission_target_ee.cons_commission_pay_on')
        cons_commission_pay_by = ir_config_obj.sudo().get_param('aspl_sales_commission_target_ee.cons_commission_pay_by')
        dist_commission_pay_on = ir_config_obj.sudo().get_param('aspl_sales_commission_target_ee.dist_commission_pay_on')
        dist_commission_pay_by = ir_config_obj.sudo().get_param('aspl_sales_commission_target_ee.dist_commission_pay_by')

        if commission_pay_on == 'order_confirm':
            for sale_id in self.filtered(lambda sale: sale.state == 'sale'):
                sale_id.order_calculate_commission(ptype='sales_person', commission_pay_by=commission_pay_by)

        if cons_commission_pay_on == 'order_confirm':
            for sale_id in self.filtered(lambda sale: sale.state == 'sale'):
                sale_id.order_calculate_commission(ptype='consultant', commission_pay_by=cons_commission_pay_by)

        if dist_commission_pay_on == 'order_confirm':
            for sale_id in self.filtered(lambda sale: sale.state == 'sale'):
                sale_id.order_calculate_commission(ptype='distributor', commission_pay_by=dist_commission_pay_by)

        return res

    @api.model
    def fields_view_get(self, view_id=None, view_type='form', toolbar=False, submenu=False):
        res = super(SaleOrder, self).fields_view_get(view_id=view_id, view_type=view_type, toolbar=toolbar,
                                                      submenu=submenu)
        if view_type == 'form':
            if not self.env.user.has_group('sales_team.group_sale_manager'):
                doc = etree.XML(res['arch'])
                if doc.xpath("//field[@name='commission_calc']"):
                    node = doc.xpath("//field[@name='commission_calc']")[0]
                    node.set('readonly', '1')
                    setup_modifiers(node, res['fields']['commission_calc'])
                if doc.xpath("//field[@name='commission_role_ids']"):
                    node = doc.xpath("//field[@name='commission_role_ids']")[0]
                    node.set('readonly', '1')
                    setup_modifiers(node, res['fields']['commission_role_ids'])
                res['arch'] = etree.tostring(doc)
        return res

    def job_related_users(self, jobid):
        if jobid:
            empids = self.env['hr.employee'].search([('user_id', '!=', False), ('job_id', '=', jobid.id)])
            return [emp.user_id.id for emp in empids]
        return False

    @api.one
    @api.depends('partner_id', 'team_id', 'user_id', 'commission_calc', 'amount_total', 'commission_role_ids', 'consultant_ids')
    def _compute_commission_data(self):
        member_lst = []
        details_lst = []
        ir_config_obj = self.env['ir.config_parameter']
        sale_comm_inc_amount = ir_config_obj.sudo().get_param('aspl_sales_commission_target_ee.commission_included_amount') if ir_config_obj.sudo().get_param('aspl_sales_commission_target_ee.commission_included_amount') else 'without_tax'
        dist_comm_inc_amount = ir_config_obj.sudo().get_param('aspl_sales_commission_target_ee.dist_commission_included_amount') if ir_config_obj.sudo().get_param('aspl_sales_commission_target_ee.dist_commission_included_amount') else 'without_tax'
        cons_comm_inc_amount = ir_config_obj.sudo().get_param('aspl_sales_commission_target_ee.cons_commission_included_amount') if ir_config_obj.sudo().get_param('aspl_sales_commission_target_ee.cons_commission_included_amount') else 'without_tax'
        commission_pay_on = ir_config_obj.sudo().get_param('aspl_sales_commission_target_ee.commission_pay_on')
        cons_commission_pay_on = ir_config_obj.sudo().get_param('aspl_sales_commission_target_ee.cons_commission_pay_on')
        dist_commission_pay_on = ir_config_obj.sudo().get_param('aspl_sales_commission_target_ee.dist_commission_pay_on')
        emp_id = self.env['hr.employee'].search([('user_id', '=', self.user_id.id)], limit=1)
        for role in self.commission_role_ids:
            if self.commission_calc == 'product':
                for soline in self.order_line:
                    if role.name == 'Sales Person' and commission_pay_on == 'order_confirm':
                        for lineid in soline.product_id.product_comm_ids:
                            lines = {'user_id': self.user_id.id, 'job_id': emp_id.job_id.id,
                                     'commission_type': 'sales_person', 'user_sales_amount': 0.00}
                            details = {'name': soline.product_id.display_name, 'person': self.user_id.partner_id.id,
                                       'role': role.id, 'type': lineid.compute_price_type,
                                       'commission': lineid.commission}
                            if (lineid.user_ids and self.user_id.id in [user.id for user in lineid.user_ids]) or \
                               (lineid.job_id and not lineid.user_ids and self.user_id.id in self.job_related_users(lineid.job_id)):
                                    lines['commission'] = soline.price_subtotal * lineid.commission / 100 if lineid.compute_price_type == 'per' else lineid.commission * soline.product_uom_qty
                                    lines['user_sales_amount'] += soline.price_subtotal
                                    member_lst.append(lines)
                                    details['commission_amount'] = lines['commission']
                                    details_lst.append(details)
                                    break
                    elif role.name == 'Consultant' and cons_commission_pay_on == 'order_confirm':
                        for consultant in self.consultant_ids.filtered(lambda line: line.is_consultant):
                            for lineid in soline.product_id.product_cons_comm_ids:
                                if consultant.id == lineid.partner_id.id:
                                    member_lst.append({'partner_id': consultant.id,
                                                       'commission': soline.price_subtotal * lineid.commission / 100 if lineid.compute_price_type == 'per' else lineid.commission * soline.product_uom_qty,
                                                       'commission_type': 'consultant'})
                                    details_lst.append(
                                        {'name': soline.product_id.display_name, 'person': consultant.id,
                                         'role': role.id, 'type': lineid.compute_price_type,
                                         'commission': lineid.commission,
                                         'commission_amount': soline.price_subtotal * lineid.commission / 100 if lineid.compute_price_type == 'per' else lineid.commission * soline.product_uom_qty})
                                    break
                    elif role.name == 'Distributor' and dist_commission_pay_on == 'order_confirm' and self.partner_id and self.partner_id.is_distributor:
                        for lineid in soline.product_id.product_dist_comm_ids.filtered(lambda line: line.partner_id.id == self.partner_id.id):
                            member_lst.append({'partner_id': self.partner_id.id,
                                               'commission': soline.price_subtotal * lineid.commission / 100 if lineid.compute_price_type == 'per' else lineid.commission * soline.product_uom_qty,
                                               'commission_type': 'distributor'})
                            details_lst.append({'name': soline.product_id.display_name, 'person': self.partner_id.id,
                                 'role': role.id, 'type': lineid.compute_price_type,
                                 'commission': lineid.commission,
                                 'commission_amount': soline.price_subtotal * lineid.commission / 100 if lineid.compute_price_type == 'per' else lineid.commission * soline.product_uom_qty})
                            break
            elif self.commission_calc == 'product_categ':
                for soline in self.order_line:
                    if role.name == 'Sales Person' and commission_pay_on == 'order_confirm':
                        for lineid in soline.product_id.categ_id.prod_categ_comm_ids:
                            lines = {'user_id': self.user_id.id, 'job_id': emp_id.job_id.id, 'commission_type': 'sales_person',
                            'user_sales_amount': 0.00}
                            details = {'name': soline.product_id.categ_id.display_name, 'person': self.user_id.partner_id.id, 'role': role.id, 'type': lineid.compute_price_type, 'commission': lineid.commission}
                            if (lineid.user_ids and self.user_id.id in [user.id for user in lineid.user_ids]) or \
                                    (lineid.job_id and not lineid.user_ids and self.user_id.id in self.job_related_users(lineid.job_id)):
                                lines['commission'] = soline.price_subtotal * lineid.commission / 100 if lineid.compute_price_type == 'per' else lineid.commission * soline.product_uom_qty
                                lines['user_sales_amount'] += soline.price_subtotal
                                member_lst.append(lines)
                                details['commission_amount'] = lines['commission']
                                details_lst.append(details)
                                break
                    elif role.name == 'Consultant' and cons_commission_pay_on == 'order_confirm':
                        for consultant in self.consultant_ids.filtered(lambda line: line.is_consultant):
                            for lineid in soline.product_id.categ_id.prod_categ_cons_comm_ids:
                                if consultant.id == lineid.partner_id.id:
                                    member_lst.append({'partner_id': consultant.id, 'commission':soline.price_subtotal * lineid.commission / 100 if lineid.compute_price_type == 'per' else lineid.commission * soline.product_uom_qty,
                                                       'commission_type': 'consultant'})
                                    details_lst.append({'name': soline.product_id.categ_id.display_name, 'person': consultant.id,
                                         'role': role.id, 'type': lineid.compute_price_type, 'commission': lineid.commission,
                                        'commission_amount': soline.price_subtotal * lineid.commission / 100 if lineid.compute_price_type == 'per' else lineid.commission * soline.product_uom_qty})
                                    break
                    elif role.name == 'Distributor' and dist_commission_pay_on == 'order_confirm' and self.partner_id and self.partner_id.is_distributor:
                        for lineid in soline.product_id.categ_id.prod_categ_dist_comm_ids.filtered(lambda line: line.partner_id.id == self.partner_id.id):
                            member_lst.append({'partner_id': self.partner_id.id, 'commission': soline.price_subtotal * lineid.commission / 100 if lineid.compute_price_type == 'per' else lineid.commission * soline.product_uom_qty,
                                               'commission_type': 'distributor'})
                            details_lst.append({'name': soline.product_id.categ_id.display_name, 'person': self.partner_id.id,
                                 'role': role.id, 'type': lineid.compute_price_type, 'commission': lineid.commission,
                                'commission_amount': soline.price_subtotal * lineid.commission / 100 if lineid.compute_price_type == 'per' else lineid.commission * soline.product_uom_qty})
                            break
            elif self.commission_calc == 'customer' and self.partner_id:
                if role.name == 'Sales Person' and commission_pay_on == 'order_confirm':
                    for lineid in self.partner_id.comm_ids:
                        lines = {'user_id': self.user_id.id, 'job_id': emp_id.job_id.id, 'commission_type': 'sales_person'}
                        details = {'name': self.partner_id.name, 'person': self.user_id.partner_id.id, 'role': role.id, 'type': lineid.compute_price_type,'commission': lineid.commission}
                        if (lineid.user_ids and self.user_id.id in [user.id for user in lineid.user_ids]) or \
                                (lineid.job_id and not lineid.user_ids and self.user_id.id in self.job_related_users(lineid.job_id)):
                            if sale_comm_inc_amount == 'with_tax':
                                lines['commission'] = self.amount_total * lineid.commission / 100 if lineid.compute_price_type == 'per' else lineid.commission
                                lines['user_sales_amount'] = self.amount_total
                            elif sale_comm_inc_amount == 'without_tax':
                                lines['commission'] = self.amount_untaxed * lineid.commission / 100 if lineid.compute_price_type == 'per' else lineid.commission
                                lines['user_sales_amount'] = self.amount_untaxed
                            member_lst.append(lines)
                            details['commission_amount'] = lines['commission']
                            details_lst.append(details)
                            break
                elif role.name == 'Consultant' and cons_commission_pay_on == 'order_confirm':
                    for consultant in self.consultant_ids.filtered(lambda line: line.is_consultant):
                        for lineid in self.partner_id.consultant_comm_ids:
                            if consultant.id == lineid.partner_id.id:
                                lines = {'partner_id': consultant.id, 'commission_type': 'consultant'}
                                if cons_comm_inc_amount == 'with_tax':
                                    lines['commission'] = self.amount_total * lineid.commission / 100 if lineid.compute_price_type == 'per' else lineid.commission
                                elif cons_comm_inc_amount == 'without_tax':
                                    lines['commission'] = self.amount_untaxed * lineid.commission / 100 if lineid.compute_price_type == 'per' else lineid.commission
                                member_lst.append(lines)
                                details_lst.append({'name': self.partner_id.name, 'person': consultant.id, 'role': role.id, 'type': lineid.compute_price_type,'commission': lineid.commission,
                                                    'commission_amount':lines['commission']})
                                break
                elif role.name == 'Distributor' and dist_commission_pay_on == 'order_confirm' and self.partner_id and self.partner_id.is_distributor:
                    for lineid in self.partner_id.distributor_comm_ids.filtered(lambda line: line.partner_id.id == self.partner_id.id):
                        lines = {'partner_id': self.partner_id.id, 'commission_type': 'distributor'}
                        if dist_comm_inc_amount == 'with_tax':
                            lines['commission'] = self.amount_total * lineid.commission / 100 if lineid.compute_price_type == 'per' else lineid.commission
                        elif dist_comm_inc_amount == 'without_tax':
                            lines['commission'] = self.amount_untaxed * lineid.commission / 100 if lineid.compute_price_type == 'per' else lineid.commission
                        member_lst.append(lines)
                        details_lst.append({'name': self.partner_id.name, 'person': self.partner_id.id,'role': role.id, 'type': lineid.compute_price_type,'commission': lineid.commission,
                                            'commission_amount': lines['commission']})
                        break
            elif self.commission_calc == 'sale_team' and self.team_id:
                if role.name == 'Sales Person' and commission_pay_on == 'order_confirm':
                    for lineid in self.team_id.sale_team_comm_ids:
                        lines = {'user_id': self.user_id.id, 'job_id': emp_id.job_id.id, 'commission_type': 'sales_person'}
                        details = {'name': self.team_id.display_name, 'person': self.user_id.partner_id.id, 'role': role.id, 'type': lineid.compute_price_type, 'commission': lineid.commission}
                        if (lineid.user_ids and self.user_id.id in [user.id for user in lineid.user_ids]) or \
                                (lineid.job_id and not lineid.user_ids and self.user_id.id in self.job_related_users(lineid.job_id)):
                            if sale_comm_inc_amount == 'with_tax':
                                lines['commission'] = self.amount_total * lineid.commission / 100 if lineid.compute_price_type == 'per' else lineid.commission
                                lines['user_sales_amount'] = self.amount_total
                            elif sale_comm_inc_amount == 'without_tax':
                                lines['commission'] = self.amount_untaxed * lineid.commission / 100 if lineid.compute_price_type == 'per' else lineid.commission
                                lines['user_sales_amount'] = self.amount_untaxed
                            member_lst.append(lines)
                            details['commission_amount'] = lines['commission']
                            details_lst.append(details)
                            break
                elif role.name == 'Consultant' and cons_commission_pay_on == 'order_confirm':
                    for consultant in self.consultant_ids.filtered(lambda line: line.is_consultant):
                        for lineid in self.team_id.sale_team_cons_comm_ids:
                            if consultant.id == lineid.partner_id.id:
                                lines = {'partner_id': consultant.id, 'commission_type': 'consultant'}
                                if cons_comm_inc_amount == 'with_tax':
                                    lines['commission'] = self.amount_total * lineid.commission / 100 if lineid.compute_price_type == 'per' else lineid.commission
                                elif cons_comm_inc_amount == 'without_tax':
                                    lines['commission'] = self.amount_untaxed * lineid.commission / 100 if lineid.compute_price_type == 'per' else lineid.commission
                                member_lst.append(lines)
                                details_lst.append({'name': self.team_id.display_name, 'person': consultant.id, 'role': role.id, 'type': lineid.compute_price_type,'commission': lineid.commission,
                                                    'commission_amount': lines['commission']})
                                break
                elif role.name == 'Distributor' and dist_commission_pay_on == 'order_confirm' and self.partner_id and self.partner_id.is_distributor:
                    for lineid in self.team_id.sale_team_dist_comm_ids.filtered(lambda line: line.partner_id.id == self.partner_id.id):
                        lines = {'partner_id': self.partner_id.id, 'commission_type': 'distributor'}
                        if dist_comm_inc_amount == 'with_tax':
                            lines['commission'] = self.amount_total * lineid.commission / 100 if lineid.compute_price_type == 'per' else lineid.commission
                        elif dist_comm_inc_amount == 'without_tax':
                            lines['commission'] = self.amount_untaxed * lineid.commission / 100 if lineid.compute_price_type == 'per' else lineid.commission
                        member_lst.append(lines)
                        details_lst.append({'name': self.team_id.display_name, 'person': self.partner_id.id, 'role': role.id, 'type': lineid.compute_price_type,'commission': lineid.commission,
                                            'commission_amount': lines['commission']})
                        break
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

    sale_order_comm_ids = fields.One2many('sales.order.commission', 'order_id', string="Sale Order Commission",
                                          compute="_compute_commission_data", store=True)
    details_ids = fields.One2many('commission.calculation.details', 'so_order_id', string="Details")
    commission_calc = fields.Selection([('sale_team', 'Sales Team'), ('customer', 'Customer'),
                                        ('product_categ', 'Product Category'),
                                        ('product', 'Product')], string="Commission Calculation",copy=False)
    commission_role_ids = fields.Many2many('sales.commission.role', string="Commission Role(s)", default= default_commission_role_id)
    consultant_ids = fields.Many2many('res.partner', string="Consultants", domain=[('is_consultant', '=', True)])

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
