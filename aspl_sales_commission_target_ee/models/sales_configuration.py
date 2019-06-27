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
from odoo.exceptions import Warning


class SalesPersonConfiguration(models.TransientModel):
    _description = 'Sale Person Configuration'
    _name = 'sales.person.configuration'

    sales_person_all = fields.Boolean(string='All Sales Person')
    sales_person_job_ids = fields.Many2many('hr.job', 'sales_job_rel', string="Job Position(s)")
    sales_person_ids = fields.Many2many('res.users', string="User(s)")
    to_customer = fields.Boolean(string='Customer')
    to_product = fields.Boolean(string='Product')
    to_product_categ = fields.Boolean(string='Product Category')
    to_sales_team = fields.Boolean(string='Sales Team')
    all_customers = fields.Boolean(string='All Customers')
    all_products = fields.Boolean(string='All Products')
    all_categories = fields.Boolean(string='All Categories')
    all_sales_teams = fields.Boolean(string='All Sales Teams')
    product_ids = fields.Many2many('product.product', string="Product(s)")
    category_ids = fields.Many2many('product.category', string="Product Category(s)")
    user_ids = fields.Many2many('res.partner', 'par_rel', string="Customer(s)")
    team_ids = fields.Many2many('crm.team', string="Sale Team(s)")
    product_compute_price_type = fields.Selection([('fix_price', 'Fix Price'), ('per', 'Percentage')],
                                                  string="Product Compute Price", default="per")
    product_commission = fields.Float(string="Product Commission")
    product_categ_compute_price_type = fields.Selection([('fix_price', 'Fix Price'), ('per', 'Percentage')],
                                                        string="Product Category Compute Price", default="per")
    product_categ_commission = fields.Float(string="Product Category Commission")
    customer_compute_price_type = fields.Selection([('fix_price', 'Fix Price'), ('per', 'Percentage')],
                                                   string="Customer Compute Price", default="per")
    customer_commission = fields.Float(string="Customer Commission")
    team_compute_price_type = fields.Selection([('fix_price', 'Fix Price'), ('per', 'Percentage')],
                                               string="Sales Team Compute Price", default="per")
    team_commission = fields.Float(string="Sales Team Commission")

    @api.constrains('product_commission', 'product_compute_price_type')
    def check_product_commission(self):
        if self.product_commission and self.product_compute_price_type == 'per' and (
                self.product_commission < 0.0 or self.product_commission > 100):
            raise Warning(_('Commission value for Percentage type must be between 0 to 100.'))

    @api.constrains('product_categ_commission', 'product_categ_compute_price_type')
    def check_product_categ_commission(self):
        if self.product_categ_commission and self.product_categ_compute_price_type == 'per' and (
                self.product_categ_commission < 0.0 or self.product_categ_commission > 100):
            raise Warning(_('Commission value for Percentage type must be between 0 to 100.'))

    @api.constrains('customer_commission', 'customer_compute_price_type')
    def check_customers_commission(self):
        if self.customer_commission and self.customer_compute_price_type == 'per' and (
                self.customer_commission < 0.0 or self.customer_commission > 100):
            raise Warning(_('Commission value for Percentage type must be between 0 to 100.'))

    @api.constrains('team_commission', 'team_compute_price_type')
    def check_customer_commission(self):
        if self.team_commission and self.team_compute_price_type == 'per' and (
                self.team_commission < 0.0 or self.team_commission > 100):
            raise Warning(_('Commission value for Percentage type must be between 0 to 100.'))

    def job_related_users(self, jobid):
        if jobid:
            empids = self.env['hr.employee'].search([('user_id', '!=', False), ('job_id', '=', jobid.id)])
            return [emp.user_id.id for emp in empids]
        return False

    @api.multi
    def apply_config(self):
        job_ids = self.sales_person_job_ids if not self.sales_person_all else self.env['hr.job'].search([])
        user_ids = self.sales_person_ids if not self.sales_person_all else self.env['res.users'].search([])
        product_ids = self.product_ids if not self.all_products else self.env['product.product'].search([])
        category_ids = self.category_ids if not self.all_categories else self.env['product.category'].search([])
        usr_ids = self.user_ids if not self.all_customers else self.env['res.partner'].search([])
        team_ids = self.team_ids if not self.all_sales_teams else self.env['crm.team'].search([])
        if job_ids or user_ids:
            vals = {}
            for job in job_ids:
                vals.update({job: self.env['res.users']})
                emp_user_lst = self.job_related_users(job)
                for userid in self.env['res.users'].browse(emp_user_lst):
                    if userid in user_ids:
                        vals[job] += userid
                        user_ids -= userid
            for user in user_ids:
                vals.update({user: []})
            for key, value in vals.items():
                if self.to_product:
                    for product in product_ids:
                        if key._name == 'hr.job':
                            product.write({'product_comm_ids': [(0, 0, {'job_id': key.id,
                                                                        'user_ids': [(6, 0, [x.id for x in value])],
                                                                        'compute_price_type': self.product_compute_price_type,
                                                                        'commission': self.product_commission
                                                                        })]})
                        elif key._name == 'res.users':
                            product.write({'product_comm_ids': [(0, 0, {'job_id': False,
                                                                        'user_ids': [(6, 0, [key.id])],
                                                                        'compute_price_type': self.product_compute_price_type,
                                                                        'commission': self.product_commission
                                                                        })]})
                if self.to_product_categ:
                    for category in category_ids:
                        if key._name == 'hr.job':
                            category.write({'prod_categ_comm_ids': [(0, 0, {'job_id': key.id,
                                                                            'user_ids': [(6, 0, [x.id for x in value])],
                                                                            'compute_price_type': self.product_categ_compute_price_type,
                                                                            'commission': self.product_categ_commission
                                                                            })]})
                        elif key._name == 'res.users':
                            category.write({'prod_categ_comm_ids': [(0, 0, {'job_id': False,
                                                                            'user_ids': [(6, 0, [key.id])],
                                                                            'compute_price_type': self.product_categ_compute_price_type,
                                                                            'commission': self.product_categ_commission
                                                                            })]})
                if self.to_sales_team:
                    for team in team_ids:
                        if key._name == 'hr.job':
                            team.write({'sale_team_comm_ids': [(0, 0, {'job_id': key.id,
                                                                       'user_ids': [(6, 0, [x.id for x in value])],
                                                                       'compute_price_type': self.team_compute_price_type,
                                                                       'commission': self.team_commission
                                                                       })]})
                        elif key._name == 'res.users':
                            team.write({'sale_team_comm_ids': [(0, 0, {'job_id': False,
                                                                       'user_ids': [(6, 0, [key.id])],
                                                                       'compute_price_type': self.team_compute_price_type,
                                                                       'commission': self.team_commission
                                                                       })]})

                if self.to_customer:
                    for customer in usr_ids:
                        if key._name == 'hr.job':
                            customer.write({'comm_ids': [(0, 0, {'job_id': key.id,
                                                                 'user_ids': [(6, 0, [x.id for x in value])],
                                                                 'compute_price_type': self.customer_compute_price_type,
                                                                 'commission': self.customer_commission
                                                                 })]})
                        elif key._name == 'res.users':
                            customer.write({'comm_ids': [(0, 0, {'job_id': False,
                                                                 'user_ids': [(6, 0, [key.id])],
                                                                 'compute_price_type': self.customer_compute_price_type,
                                                                 'commission': self.customer_commission
                                                                 })]})
        else:
            raise Warning(_('Please select Sales Person to generate commission calculation data.'))

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
