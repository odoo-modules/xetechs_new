# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models


class Project(models.Model):
    _inherit = 'project.project'

    issue_count = fields.Integer(compute='_compute_issue_count', string="Issues Count")
    issue_ids = fields.One2many('project.issue', 'project_id', string="Issues", domain=['|', ('stage_id.fold', '=', False), ('stage_id', '=', False)])
    label_issues = fields.Char(string='Use Issues as', help="Customize the issues label, for example to call them cases.", default='Issues')

    @api.model
    def _get_alias_models(self):
        res = super(Project, self)._get_alias_models()
        res.append(("project.issue", "Issues"))
        return res

    @api.multi
    def _compute_issue_count(self):
        for project in self:
            project.issue_count = self.env['project.issue'].search_count([('project_id', '=', project.id), '|', ('stage_id.fold', '=', False), ('stage_id', '=', False)])

    @api.multi
    def write(self, vals):
        res = super(Project, self).write(vals)
        if 'active' in vals:
            # archiving/unarchiving a project does it on its issues, too
            issues = self.with_context(active_test=False).mapped('issue_ids')
            issues.write({'active': vals['active']})
        return res
