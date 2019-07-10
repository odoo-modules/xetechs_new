# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _


class Task(models.Model):
    _inherit = "project.task"

    def action_create_issue(self):
        # ctx = dict(self.env.context or {})
        # print('ctxxxxxx', ctx, self.id)
        # ctx.update({'project_id': self.project_id.id})
        view = self.env.ref('project_issue.project_issue_form_view')
        return {
            'name': _('Create Issue'),
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'project.issue',
            'views': [(view.id, 'form')],
            'view_id': view.id,
            'target': 'new',
            # 'context': ctx,
        }
