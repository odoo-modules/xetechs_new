# -*- coding: utf-8 -*-

from odoo.exceptions import ValidationError,UserError
from datetime import datetime
from dateutil.relativedelta import relativedelta
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT
from odoo import models, fields, api, _
import time


class Account_Invoice_EMI(models.Model):
    _name = "account.invoice.emi"

    name = fields.Char(string='Account Invoice EMI', required=True, copy=False, readonly=True, index=True, default=lambda self: _('New'))
    so_id = fields.Many2one('sale.order', string="Sales Order", required=True, domain="[('state', '=', 'done')]")
    type = fields.Selection([
            ('fixed', 'Fixed'),
            ('manual', 'Manual'),
        ], string="EMI Type", default="manual")
    total = fields.Integer(string="Total EMI")
    total_emi = fields.Integer(string="Total EMI")
    paid_total = fields.Integer(string="Total Paid EMI")
    interest = fields.Float(string="Interest Rate")
    inv_emi_lines = fields.One2many('account.invoice.emi.line', 'acc_inv_emi_id', string="EMI Lines")
    currency_id = fields.Many2one(related="so_id.currency_id", string="Currency", readonly=True, required=True)
    so_amount = fields.Monetary(related="so_id.amount_total", string='SO Amount', store="True")
    state = fields.Selection([
            ('draft', 'Draft'),
            ('confirm', 'Confirm'),
            ('process', 'Process'),
            ('done', 'Done'),
        ], string="State", default="draft")
    partner_id = fields.Many2one('res.partner', string='Customer')
    project_name = fields.Char(string='Project Name', copy=False, readonly=True, index=True, default=lambda self: _('New'))


    @api.onchange('interest')
    def onchange_total_interest(self):
        if self.interest < 0:
            raise ValidationError(_("Interest must be positive value"))

    @api.onchange('total')
    def onchange_total_total(self):
        if self.type == 'fixed':
            if self.total <= 0:
                raise ValidationError(_("Total Invoice must be > 0"))

    @api.onchange('type')
    def onchange_type(self):
        if self.type:
            self.total = 0
            self.interest = 0
    
    @api.model
    def create(self, vals):
        if vals.get('name', _('New')) == _('New'):
            if 'company_id' in vals:
                vals['name'] = self.env['ir.sequence'].with_context(force_company=vals['company_id']).next_by_code('account.invoice.emi') or _('New')
            else:
                vals['name'] = self.env['ir.sequence'].next_by_code('account.invoice.emi') or _('New')
        result = super(Account_Invoice_EMI, self).create(vals)
        result.project_name = 'Project Name'
        result.partner_id = result.so_id.partner_id.id
        return result

    @api.multi
    def name_get(self):
        result = []
        for rec in self:
            name = rec.so_id.name + '-' + rec.name
            result.append((rec.id, name))
        return result

    def action_confirm(self):
        if not self.so_id:
            raise ValidationError(_("Please select sales order"))
        if self.search([('so_id', '=', self.so_id.id), ('state', '=', 'confirm'), ('id', '!=', self.id)]):
            raise ValidationError(_("You can't confirm the Account invoice EMI record because same sales order selected confirm record exists."))
        if self.type == 'fixed':
            if self.total <= 0:
                raise ValidationError(_("Total Invoice must be > 0"))
            invoice = self.so_amount / self.total
            interest = (invoice * self.interest)/100
            line_data = self.inv_emi_lines
            self.total_emi = self.total
            date = datetime.now()
            for t in range(self.total):
                line = line_data.new()
                line.acc_inv_emi_id = self.id
                line.sequence = t + 1
                line.date = date.date()
                line.inv_amount = invoice
                line.interest_amount = interest
                line.total = interest + invoice
                line.state = 'draft'
                self.inv_emi_lines = self.inv_emi_lines | line
                date = datetime.strptime((date+relativedelta(months=1)).strftime(DEFAULT_SERVER_DATE_FORMAT), DEFAULT_SERVER_DATE_FORMAT)
        else:
            self.total_emi = len(self.inv_emi_lines.ids) 
        total = sum(rec.inv_amount for rec in self.inv_emi_lines)
        self.partner_id = self.so_id.partner_id.id
        if total != self.so_amount:
            raise ValidationError(_("Total amount of  EMI amount must be Equal to sale order amount "))
        self.so_id.write({'emi_unpaid': len(self.inv_emi_lines.ids),
                          'is_emi_created': True,
                          'account_invoice_emi_id':self.id
                           })
        return self.write({'state': 'confirm'})

    @api.multi
    def action_process(self):
        for res in self.inv_emi_lines:
            res.state = 'to_invoice'
        return self.write({'state': 'process'})

    @api.multi
    def action_done(self):
        if not all([x.state == 'invoiced' for x in self.inv_emi_lines]):
            raise ValidationError(_("You can not set done, some EMI need to create invoice panding"))
        return self.write({'state': 'done'})


class Account_Invoice_EMI_Line(models.Model):
    _name = "account.invoice.emi.line"

    @api.depends('inv_amount', 'acc_inv_emi_id')
    def _compute_amount(self):
        """
        Compute the amounts of the EMI line.
        """
        for line in self:
            interest_amount = (line.inv_amount * line.acc_inv_emi_id.interest) / 100.0
            line.update({
                'interest_amount': interest_amount,
                'total': interest_amount + line.inv_amount,
            })

    acc_inv_emi_id = fields.Many2one('account.invoice.emi', string="Invoice EMI")
    sequence = fields.Integer(string="No.")
    date = fields.Date(string="Date")
    inv_amount = fields.Float(string="Invoice Amount")
    interest_amount = fields.Float(compute='_compute_amount', string="Interest Amount", readonly=True, store=True)
    total = fields.Float(compute='_compute_amount', string="Total", readonly=True, store=True)
    state = fields.Selection([
            ('draft', 'Draft'),
            ('to_invoice', 'To Invoice'),
            ('invoiced', 'Invoiced'),
        ], string="State", default="draft")
    invoice_id = fields.Many2one('account.invoice', string="Invoice#")

    @api.multi
    def create_invoice(self):
        product_id = self.env['ir.config_parameter'].sudo().get_param('sale.default_deposit_product_id')
        product_data = self.env['product.product'].browse(int(product_id))

        # Create deposit product if necessary
        if not product_data:
            vals = self._prepare_deposit_product()
            product_data = self.env['product.product'].create(vals)
            self.env['ir.config_parameter'].sudo().set_param('sale.default_deposit_product_id', product_data.id)

        sale_line_obj = self.env['sale.order.line']
        for order in self.acc_inv_emi_id.so_id:
            order.emi_paid += 1
            amount = self.inv_amount + self.interest_amount
            if product_data.invoice_policy != 'order':
                raise UserError(_('The product used to invoice a down payment should have an invoice policy set to "Ordered quantities". Please update your deposit product to be able to create a deposit invoice.'))
            if product_data.type != 'service':
                raise UserError(_("The product used to invoice a down payment should be of type 'Service'. Please use another product or update this product."))
            taxes = product_data.taxes_id.filtered(lambda r: not order.company_id or r.company_id == order.company_id)
            if order.fiscal_position_id and taxes:
                tax_ids = order.fiscal_position_id.map_tax(taxes, product_data, order.partner_shipping_id).ids
            else:
                tax_ids = taxes.ids
            context = {'lang': order.partner_id.lang}
            analytic_tag_ids = []
            for line in order.order_line:
                analytic_tag_ids = [(4, analytic_tag.id, None) for analytic_tag in line.analytic_tag_ids]
            so_line = sale_line_obj.create({
                'name': _('%s : EMI %s / %s') % (product_data.name, order.emi_paid, order.emi_unpaid),
                'price_unit': amount,
                'product_uom_qty': 0.0,
                'order_id': order.id,
                'discount': 0.0,
                'product_uom': product_data.uom_id.id,
                'product_id': product_data.id,
                'analytic_tag_ids': analytic_tag_ids,
                'tax_id': [(6, 0, tax_ids)],
                'is_downpayment': True,
            })
            del context
            inv_obj = self.env['account.invoice']
            ir_property_obj = self.env['ir.property']

            account_id = False
            if product_data.id:
                account_id = order.fiscal_position_id.map_account(product_data.property_account_income_id or product_data.categ_id.property_account_income_categ_id).id
            if not account_id:
                inc_acc = ir_property_obj.get('property_account_income_categ_id', 'product.category')
                account_id = order.fiscal_position_id.map_account(inc_acc).id if inc_acc else False
            if not account_id:
                raise UserError(
                    _('There is no income account defined for this product: "%s". You may have to install a chart of account from Accounting app, settings menu.') %
                    (self.product_id.name,))

            if self.inv_amount <= 0.00:
                raise UserError(_('The value of the down payment amount must be positive.'))
            context = {'lang': order.partner_id.lang}
            name = _('%s : EMI %s / %s') % (product_data.name, order.emi_paid, order.emi_unpaid)
            invoice = inv_obj.create({
            'name': order.client_order_ref or order.name,
            'origin': order.name,
            'type': 'out_invoice',
            'reference': False,
            'account_id': order.partner_id.property_account_receivable_id.id,
            'partner_id': order.partner_invoice_id.id,
            'partner_shipping_id': order.partner_shipping_id.id,
            'invoice_line_ids': [(0, 0, {
                'name': name,
                'origin': order.name,
                'account_id': account_id,
                'price_unit': amount,
                'quantity': 1.0,
                'discount': 0.0,
                'uom_id': product_data.uom_id.id,
                'product_id': product_data.id,
                'sale_line_ids': [(6, 0, [so_line.id])],
                'invoice_line_tax_ids': [(6, 0, tax_ids)],
                'analytic_tag_ids': [(6, 0, so_line.analytic_tag_ids.ids)],
                'account_analytic_id': order.analytic_account_id.id or False,
            })],
            'currency_id': order.pricelist_id.currency_id.id,
            'payment_term_id': order.payment_term_id.id,
            'fiscal_position_id': order.fiscal_position_id.id or order.partner_id.property_account_position_id.id,
            'team_id': order.team_id.id,
            'user_id': order.user_id.id,
            'comment': order.note,
            })
            invoice.compute_taxes()
            invoice.message_post_with_view('mail.message_origin_link',
                    values={'self': invoice, 'origin': order},
                    subtype_id=self.env.ref('mail.mt_note').id)
            self.invoice_id = invoice.id
            self.state = 'invoiced'
            self.acc_inv_emi_id.paid_total += 1
        if self._context.get('open_invoices', False):
            return self.acc_inv_emi_id.so_id.action_view_invoice()
        return {'type': 'ir.actions.act_window_close'}

    def _prepare_deposit_product(self):
        return {
            'name': 'Project Product',
            'type': 'service',
            'invoice_policy': 'order',
            'property_account_income_id': False,
            'taxes_id': [(6, 0, [])],
            'company_id': False,
        }
    
    @api.model
    def auto_create_invoice_emi(self):
        current_date = fields.Date.context_today(self)
        for account_inv_emi in self.search([('date', '=', current_date), ('state', '=', 'draft')]):
            account_inv_emi.create_invoice()
        return True
