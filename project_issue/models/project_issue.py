# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models, api


class ProjectIssue(models.Model):
    _name = "project.issue"
    _description = "Project Issue"

    @api.model
    def _get_default_stage_id(self):
        project_id = self.env.context.get('default_project_id')
        if not project_id:
            return False
        return self.stage_find(project_id, [('fold', '=', False)])

    name = fields.Char(string='Issue', rtrack_visibility='onchange', equired=True)
    description = fields.Text('Description', track_visibility='onchange', required=True)
    project_id = fields.Many2one('project.project', string='Project', track_visibility='onchange', index=True, required=True)
    task_id = fields.Many2one('project.task', string='Task', domain="[('project_id','=',project_id)]", required=True)
    attachment = fields.Binary(string="Attachment", track_visibility='onchange', required=True)
    file_name = fields.Char(string="File Name", track_visibility='onchange', required=True)
    issue_reported_date = fields.Date(string="Issue Reported Date", track_visibility='onchange', required=True)
    assign_to = fields.Many2one('res.users', string="Assign", track_visibility='onchange', required=True)
    due_date = fields.Date(string="Due Date", track_visibility='onchange', required=True)
    tag_ids = fields.Many2many('project.tags', string='Category', track_visibility='onchange', required=True)
    stage_id = fields.Many2one('project.task.type', string='Stage', track_visibility='onchange', index=True,
                               domain="[('project_ids', '=', project_id)]", copy=False,
                               group_expand='_read_group_stage_ids',
                               default=_get_default_stage_id)
    color = fields.Integer('Color Index')
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.user.company_id)

    @api.model
    def _read_group_stage_ids(self, stages, domain, order):
        search_domain = [('id', 'in', stages.ids)]
        # retrieve project_id from the context, add them to already fetched columns (ids)
        if 'default_project_id' in self.env.context:
            search_domain = ['|', ('project_ids', '=', self.env.context['default_project_id'])] + search_domain
        # perform search
        return stages.search(search_domain, order=order)
