# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models, api, _
from odoo.exceptions import UserError


class ProjectIssue(models.Model):
    _name = "project.issue"
    _description = "Project Issue"
    _inherit = ['mail.thread']

    # @api.model
    # def _get_default_stage_id(self):
    #     project_id = self.env.context.get('default_project_id')
    #     if not project_id:
    #         return False
    #     return self.stage_find(project_id, [('fold', '=', False)])

    name = fields.Char(string='Issue', required=True, copy=False, readonly=True, index=True, default=lambda self: _('New'), track_visibility='onchange')
    description = fields.Text('Description', track_visibility='onchange', required=True)
    project_id = fields.Many2one('project.project', string='Project', track_visibility='onchange', index=True, required=True)
    task_id = fields.Many2one('project.task', string='Task', required=True, track_visibility='onchange')
    attachment = fields.Binary(string="Attachment", track_visibility='onchange', required=True)
    file_name = fields.Char(string="File Name", track_visibility='onchange', required=True)
    issue_reported_date = fields.Date(string="Issue Reported Date", track_visibility='onchange', required=True)
    assign_to = fields.Many2one('res.users', string="Assigned To", track_visibility='onchange', required=True)
    due_date = fields.Date(string="Due Date", track_visibility='onchange', required=True)
    tag_ids = fields.Many2many('project.tags', string='Tags', track_visibility='onchange', required=True)
    stage_id = fields.Many2one('project.task.type', string='Stage', track_visibility='onchange', index=True,
                               domain="[('project_ids', '=', project_id)]", copy=False)
    color = fields.Integer('Color Index')
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.user.company_id, track_visibility='onchange')
    priority = fields.Selection([
        ('0', 'Low'),
        ('1', 'Normal'),
        ], default='0', index=True, string="Priority", track_visibility='onchange')
    issue_category = fields.Many2one('project.issue.category', string='Category', track_visibility='onchange')
    # @api.model
    # def _read_group_stage_ids(self, stages, domain, order):
    #     search_domain = [('id', 'in', stages.ids)]
    #     # retrieve project_id from the context, add them to already fetched columns (ids)
    #     if 'default_project_id' in self.env.context:
    #         search_domain = ['|', ('project_ids', '=', self.env.context['default_project_id'])] + search_domain
    #     # perform search
    #     return stages.search(search_domain, order=order)

    @api.model
    def create(self, vals):
        print(self.project_id.sequence)
        if vals.get('name', _('New')) == _('New'):
            if 'company_id' in vals:
                vals['name'] = self.env['ir.sequence'].with_context(force_company=vals['company_id']).next_by_code('project.issue') or _('New')
            else:
                vals['name'] = self.env['ir.sequence'].next_by_code('project.issue') or _('New')
        result = super(ProjectIssue, self).create(vals)
        return result

    @api.multi
    @api.depends('name', 'project_id', 'task_id')
    def name_get(self):
        result = []
        for res in self:
            name = res.project_id.name + " - " + res.task_id.name + " - " + res.name
            self.name = name
            result.append((res.id, name))
        return result


class ProjectIssueCategory(models.Model):
    _name = "project.issue.category"

    name = fields.Char('Issue Category')
