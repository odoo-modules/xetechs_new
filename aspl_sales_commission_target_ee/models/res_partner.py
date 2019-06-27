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


class ResPartner(models.Model):
    _inherit = 'res.partner'

    @api.constrains('comm_ids', 'distributor_comm_ids', 'consultant_comm_ids')
    def _check_commission_values(self):
        if self.comm_ids.filtered(lambda line: line.compute_price_type == 'per' and line.commission > 100 or line.commission < 0.0):
            raise Warning(_('Commission value for Percentage type must be between 0 to 100.'))
        if self.distributor_comm_ids.filtered(lambda line: line.compute_price_type == 'per' and line.commission > 100 or line.commission < 0.0):
            raise Warning(_('Commission value for Percentage type must be between 0 to 100.'))
        if self.consultant_comm_ids.filtered(lambda line: line.compute_price_type == 'per' and line.commission > 100 or line.commission < 0.0):
            raise Warning(_('Commission value for Percentage type must be between 0 to 100.'))

    comm_ids = fields.One2many('res.partner.commission', 'partner_id', string="Sales Commission")
    is_distributor = fields.Boolean('Is a Distributor')
    is_consultant = fields.Boolean('Is a Consultant')
    distributor_comm_ids = fields.One2many('distributor.commission', 'cons_id', string="Distributor Commission")
    consultant_comm_ids = fields.One2many('consultant.commission', 'cons_id', string="Consultant Commission")


class ResPartnerCommission(models.Model):
    _description = 'Partner Commission'
    _name = 'res.partner.commission'

    @api.onchange('job_id')
    def onchange_job_id(self):
        self.user_ids = False

    @api.onchange('commission', 'compute_price_type')
    def onchange_commission(self):
        if self.commission and self.compute_price_type == 'per' and (self.commission < 0.0 or self.commission > 100):
            raise Warning(_('Entered Commission is %s. \n Commission value for Percentage type must be between 0 to 100. ') % self.commission)

    job_id = fields.Many2one('hr.job', string="Job Position")
    user_ids = fields.Many2many('res.users', string="User(s)")
    compute_price_type = fields.Selection([('fix_price', 'Fix Price'), ('per', 'Percentage')],
                                          string="Compute Price", default="per", required=True)
    commission = fields.Float(string="Commission")
    partner_id = fields.Many2one('res.partner', string="Partner")


class DistributorCommission(models.Model):
    _description = 'Distributor Commission'
    _name = 'distributor.commission'

    @api.onchange('commission', 'compute_price_type')
    def onchange_commission(self):
        if self.commission and self.compute_price_type == 'per' and (self.commission < 0.0 or self.commission > 100):
            raise Warning(_('Entered Commission is %s. \n Commission value for Percentage type must be between 0 to 100. ') % self.commission)

    partner_id = fields.Many2one('res.partner', string="Distributor")
    compute_price_type = fields.Selection([('fix_price', 'Fix Price'), ('per', 'Percentage')],
                                          string="Compute Price", default="per", required=True)
    commission = fields.Float(string="Commission")
    cons_id = fields.Many2one('res.partner', string="Partner")


class ConsultantCommission(models.Model):
    _description = 'Consultant Commission'
    _name = 'consultant.commission'

    @api.onchange('commission', 'compute_price_type')
    def onchange_commission(self):
        if self.commission and self.compute_price_type == 'per' and (self.commission < 0.0 or self.commission > 100):
            raise Warning(_('Entered Commission is %s. \n Commission value for Percentage type must be between 0 to 100. ') % self.commission)

    partner_id = fields.Many2one('res.partner', string="Consultant")
    compute_price_type = fields.Selection([('fix_price', 'Fix Price'), ('per', 'Percentage')],
                                          string="Compute Price", default="per", required=True)
    commission = fields.Float(string="Commission")
    cons_id = fields.Many2one('res.partner', string="Partner")


class ResUsers(models.Model):
    _inherit = 'res.users'

    @api.model
    def name_search(self, name, args=None, operator='ilike', limit=100):
        if self._context.get('ctx_job_id'):
            emp_ids = self.env['hr.employee'].search([('user_id', '!=', False),
                                                      ('job_id', '=', self._context['ctx_job_id'])])
            args += [('id', 'in', [emp.user_id.id for emp in emp_ids])]
        elif self._context.get('ctx_job_ids',False) and self._context.get('ctx_job_ids')[0][2]:
            emp_ids = self.env['hr.employee'].search([('user_id', '!=', False),
                                                      ('job_id', 'in', self._context.get('ctx_job_ids')[0][2])])
            args += [('id', 'in', [emp.user_id.id for emp in emp_ids])]
        return super(ResUsers, self).name_search(name=name, args=args, operator='ilike', limit=limit)

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
