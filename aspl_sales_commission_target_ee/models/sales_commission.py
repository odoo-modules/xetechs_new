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


class SalesCommission(models.Model):
    _description = 'Sale Commission'
    _name = 'sales.commission'
    _order = 'commission_date desc'

    @api.one
    def state_cancel(self):
        if self.state == 'draft' and not self.invoice_id:
            self.state = 'cancel'

    @api.one
    def state_draft(self):
        if self.state == 'cancel':
            self.state = 'draft'

    @api.model
    def generate_sale_invoice(self):
        commission_ids = self.env['sales.commission'].search([('state', '=', 'draft'), ('pay_by', '=', 'invoice'),
                                                              '|', ('invoice_id', '=', False), ('invoice_id.state', '=', 'cancel')])

        for user in set([comm.user_id.id for comm in commission_ids.filtered(lambda comm: comm.type == 'sales_person')]):
            rec_id = self.env['sales.commission.payment'].create({'user_id': user, 'type': 'sales_person'})
            rec_id.with_context({'commission_ids': commission_ids.filtered(lambda line: line.user_id.id == user)}).generate_invoice()

        for cons in set([comm.cons_id.id for comm in commission_ids.filtered(lambda comm: comm.type == 'consultant')]):
            rec_id = self.env['sales.commission.payment'].create({'consultant_id': cons, 'type': 'consultant'})
            rec_id.with_context({'commission_ids': commission_ids.filtered(lambda line: line.cons_id.id == cons)}).generate_invoice()

        for dist in set([comm.cons_id.id for comm in commission_ids.filtered(lambda comm: comm.type == 'distributor')]):
            rec_id = self.env['sales.commission.payment'].create({'distributor_id': dist, 'type': 'distributor'})
            rec_id.with_context({'commission_ids': commission_ids.filtered(lambda line: line.cons_id.id == dist)}).generate_invoice()

    name = fields.Char(string="Source Document")
    sale_id = fields.Many2one('sale.order', string="SO Reference")
    type = fields.Selection([('sales_person', 'Sales Person'), ('consultant', 'Consultant'),
                             ('distributor', 'Distributor')], string="Type")
    user_id = fields.Many2one('res.users', string="User")
    cons_id = fields.Many2one('res.partner', string="Consultant/Distributor")
    client = fields.Many2one('res.partner', string="Client")
    when_paid = fields.Datetime(string="Paid Date")
    commission_date = fields.Date(string="Commission Date")
    amount = fields.Float(string="Commission Amount")
    pay_by = fields.Selection([('salary', 'Salary'), ('invoice', 'Invoice')], string="Pay By", default="invoice")
    state = fields.Selection([('draft', 'Draft'), ('paid', 'Paid'),
                              ('cancel', 'Cancel'), ('invoiced', 'Invoiced')], string="State", default='draft')
    invoice_id = fields.Many2one('account.invoice', string="Invoice")
    reference_invoice_id = fields.Many2one('account.invoice', string='Reference')
    user_sales_amount = fields.Float(string='Sales Amount')
    payslip_id = fields.Many2one('hr.payslip', string="Payslip")

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
