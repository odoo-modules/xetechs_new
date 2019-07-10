# -*- coding: utf-8 -*-

from odoo.exceptions import ValidationError, UserError
from datetime import datetime
from dateutil.relativedelta import relativedelta
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT
from odoo import models, fields, api, _


class Account_Invoice_EMI(models.Model):
    _name = "account.invoice.emi"

    @api.depends('so_id')
    def _compute_sales_order_amount(self):
        """
        Compute the amounts of the Sales Order line.
        """
        for line in self:
            so_line_amount = 0.0
            down_amount = 0.0
            if line.so_id:
                for so_line in line.so_id.order_line:
                    if not so_line.is_downpayment:
                        so_line_amount += so_line.price_subtotal
                    else:
                        down_amount += so_line.price_unit
            line.update({
                'so_amount': so_line_amount - down_amount,
            })

    @api.depends('so_id.invoice_ids', 'inv_emi_lines.state', 'state')
    def get_total_invoice(self):
        for res in self:
            res.total_invoice = len(res.so_id.mapped('invoice_ids'))
            res.emi_amount = round(sum([x.inv_amount for x in res.inv_emi_lines]), 2)
            res.interest_amount = round(sum([x.interest_amount for x in res.inv_emi_lines]), 2)
            res.total_amount = res.emi_amount + res.interest_amount

    name = fields.Char(string='EMI Number', required=True, copy=False, readonly=True, index=True, default=lambda self: _('New'))
    so_id = fields.Many2one('sale.order', string="Sales Order", required=True, domain="[('state', '=', 'done')]")
    type = fields.Selection([
            ('fixed', 'Fixed'),
            ('manual', 'Manual'),
        ], string="EMI Type", default="manual",)
    total = fields.Integer(string="Total EMI")
    total_emi = fields.Integer(string="Total EMI", readonly=True)
    paid_total = fields.Integer(string="Invoiced EMI", readonly=True)
    interest = fields.Float(string="Interest Rate")
    inv_emi_lines = fields.One2many('account.invoice.emi.line', 'acc_inv_emi_id', string="EMI Lines")
    currency_id = fields.Many2one(related="so_id.currency_id", string="Currency", readonly=True, required=True)
    so_amount = fields.Float(compute='_compute_sales_order_amount', string='SO Amount', readonly=True, store=True)
    state = fields.Selection([
            ('draft', 'Draft'),
            ('confirm', 'Confirm'),
            ('to_approved', 'To Be Approved'),
            ('approved', 'Approved'),
            ('done', 'Done'),
            ('reject', 'Reject')
        ], string="State", default="draft", select=True, readonly=True, copy=False)
    partner_id = fields.Many2one(related="so_id.partner_id", string='Customer', store=True)
    project_id = fields.Many2one("project.project", string='Project Name')
    total_invoice = fields.Integer(string="Total Invoice", compute="get_total_invoice")
    emi_amount = fields.Float(string="EMI Amount", compute="get_total_invoice", store=True)
    interest_amount = fields.Float(string="EMI Interest", compute="get_total_invoice", store=True)
    total_amount = fields.Float(string="Total Amount", compute="get_total_invoice", store=True)
    journal_id = fields.Many2one('account.journal', string="Payment Journal")
    currency_id = fields.Many2one("res.currency", related='so_id.currency_id', string="Currency", readonly=True, required=True)
    start_date = fields.Date(string="Start Date")
    emi_tax_ids = fields.Many2many('account.tax', 'emi_line_tax', 'emi_line_id', 'tax_id', string='Taxes', domain=[('type_tax_use', '!=', 'none'), '|', ('active', '=', False), ('active', '=', True)])

    @api.onchange('interest')
    def onchange_total_interest(self):
        if self.interest < 0 and self.interest > 100:
            raise ValidationError(_("Interest must be positive value and lessthen 100"))

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
        self._compute_sales_order_amount()
        if self.search([('so_id', '=', self.so_id.id), ('state', '=', 'confirm'), ('id', '!=', self.id)]):
            raise ValidationError(_("You can't confirm the Account invoice EMI record because same sales order selected confirm record exists."))
        if self.type == 'fixed':
            self.make_emi_generate()
        self.total_emi = len(self.inv_emi_lines.ids)
        if len(self.inv_emi_lines) == 0:
            raise ValidationError(_("Please create some EMI"))
        total = sum(rec.inv_amount for rec in self.inv_emi_lines)
        self.partner_id = self.so_id.partner_id.id
        if round(total, 2) != self.so_amount:
            raise ValidationError(_("Total amount of  EMI amount must be Equal to sale order amount"))
        self.so_id.write({'emi_unpaid': len(self.inv_emi_lines.ids),
                          'is_emi_created': True,
                          'account_invoice_emi_id': self.id})
        return self.write({'state': 'confirm'})

    @api.multi
    def make_emi_generate(self):
        self._cr.execute("DELETE FROM account_invoice_emi_line WHERE acc_inv_emi_id=%s""" % self.id)
        if self.total <= 0:
                raise ValidationError(_("Total Invoice must be > 0"))
        invoice = self.so_amount / self.total
        interest = (invoice * self.interest)/100
        line_data = self.inv_emi_lines
        date = self.start_date
        for t in range(self.total):
            line = line_data.new()
            line.acc_inv_emi_id = self.id
            line.sequence = t + 1
            line.date = date
            line.inv_amount = invoice
            line.interest_amount = interest
            line.total = interest + invoice
            line.state = 'draft'
            self.inv_emi_lines = self.inv_emi_lines | line
            date = date + relativedelta(months=1)

    @api.multi
    def action_to_be_approved(self):
        if self.so_id:
            self._compute_sales_order_amount()
        if self.type == 'fixed':
            self.make_emi_generate()
        self.total_emi = len(self.inv_emi_lines.ids)
        if len(self.inv_emi_lines) == 0:
            raise ValidationError(_("Please create some EMI"))
        total = sum(rec.inv_amount for rec in self.inv_emi_lines)
        self.partner_id = self.so_id.partner_id.id
        if round(total, 2) != self.so_amount:
            raise ValidationError(_("Total amount of  EMI amount must be Equal to sale order amount"))
        return self.write({'state': 'to_approved'})

    @api.multi
    def action_draft(self):
        return self.write({'state': 'draft'})

    @api.multi
    def action_reject(self):
        return self.write({'state': 'reject'})

    @api.multi
    def action_approved(self):
        for res in self.inv_emi_lines:
            res.state = 'to_invoice'
        return self.write({'state': 'approved'})

    @api.multi
    def action_done(self):
        if not all([x.state == 'invoiced' for x in self.inv_emi_lines]):
            raise ValidationError(_("You can not set done, some EMI need to create invoice panding"))
        return self.write({'state': 'done'})

    @api.multi
    def action_view_invoice(self):
        invoices = self.so_id.mapped('invoice_ids')
        action = self.env.ref('account.action_invoice_tree1').read()[0]
        if len(invoices) > 1:
            action['domain'] = [('id', 'in', invoices.ids)]
        elif len(invoices) == 1:
            action['views'] = [(self.env.ref('account.invoice_form').id, 'form')]
            action['res_id'] = invoices.ids[0]
        else:
            action = {'type': 'ir.actions.act_window_close'}
        return action


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
    name = fields.Char(string="Number")
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
    sale_order_id = fields.Many2one(related="acc_inv_emi_id.so_id", string="Sale Order")
    project_id = fields.Many2one(related="acc_inv_emi_id.project_id", string="Project")
    inv_status = fields.Selection(related="invoice_id.state", string="Invoice Status")

    @api.multi
    def name_get(self):
        result = []
        for rec in self:
            name = rec.acc_inv_emi_id.name + '-' + str(rec.sequence)
            result.append((rec.id, name))
        return result

    @api.multi
    def create_invoice(self):
        product_data = self.env.ref('account_invoice_emi.service_project_product_emi')
        for order in self.acc_inv_emi_id.so_id:
            order.emi_paid += 1
            amount = self.inv_amount + self.interest_amount
            if product_data.invoice_policy != 'order':
                raise UserError(_('The product used to invoice a down payment should have an invoice policy set to "Ordered quantities". Please update your deposit product to be able to create a deposit invoice.'))
            if product_data.type != 'service':
                raise UserError(_("The product used to invoice a down payment should be of type 'Service'. Please use another product or update this product."))
            if self.acc_inv_emi_id.emi_tax_ids:
                tax_ids = self.acc_inv_emi_id.emi_tax_ids.ids
            else:
                taxes = product_data.taxes_id.filtered(lambda r: not order.company_id or r.company_id == order.company_id)
                if order.fiscal_position_id and taxes:
                    tax_ids = order.fiscal_position_id.map_tax(taxes, product_data, order.partner_shipping_id).ids
                else:
                    tax_ids = taxes.ids
            context = {'lang': order.partner_id.lang}
            analytic_tag_ids = []
            for line in order.order_line:
                analytic_tag_ids = [(4, analytic_tag.id, None) for analytic_tag in line.analytic_tag_ids]
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
            # context = {'lang': order.partner_id.lang}
            if self.acc_inv_emi_id.project_id:
                name = _('%s : EMI %s / %s') % (self.acc_inv_emi_id.project_id.name, order.emi_paid, order.emi_unpaid)
            else:
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
                    # 'sale_line_ids': [(6, 0, [so_line.id])],
                    'invoice_line_tax_ids': [(6, 0, tax_ids)],
                    'analytic_tag_ids': [(6, 0, analytic_tag_ids)],
                    'account_analytic_id': order.analytic_account_id.id or False,
                })],
                'currency_id': order.pricelist_id.currency_id.id,
                'payment_term_id': order.payment_term_id.id,
                'fiscal_position_id': order.fiscal_position_id.id or order.partner_id.property_account_position_id.id,
                'team_id': order.team_id.id,
                'user_id': order.user_id.id,
                'comment': order.note,
                'journal_id': self.acc_inv_emi_id.journal_id and self.acc_inv_emi_id.journal_id.id or False
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

    @api.model
    def auto_create_invoice_emi(self):
        current_date = fields.Date.context_today(self)
        for account_inv_emi in self.search([('date', '=', current_date), ('state', '=', 'draft')]):
            account_inv_emi.create_invoice()
        return True

    @api.multi
    def create(self, vals):
        res = super(Account_Invoice_EMI_Line, self).create(vals)
        if res.acc_inv_emi_id.type != 'fix':
            old_recoreds = self.env['account.invoice.emi.line'].search([('acc_inv_emi_id', '=', res.acc_inv_emi_id.id), ('id', '!=', res.id)])
            res.sequence = len(old_recoreds) + 1
        return res
