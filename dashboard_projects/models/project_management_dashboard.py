# -*- coding: utf-8 -*-
from openerp import api, fields, models, _
from datetime import datetime , timedelta
import calendar
from pytz import timezone
import pytz
import logging
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT
_logger = logging.getLogger(__name__)

class project_management_dashboard(models.Model):
    _name = 'project.management.dashboard'

    @api.model
    def get_all_projects(self):
        projects = self.env['project.project'].search_read(['|',('active','=',False),('active','=',True)],['id','name'])
        return projects
    
    @api.model
    def get_projects_dashboard_data(self,project_id):
        total_clients = self.get_total_clients(project_id)
        total_employees = self.get_total_employees(project_id)
        total_projects = self.get_total_projects(project_id)
        total_paid_invoice = self.get_total_paid_invoice(project_id)
        total_hour_logged = self.get_total_hour_logged(project_id)
        total_pending_tasks = self.get_total_pending_tasks(project_id)
        total_complete_tasks = self.get_total_complete_tasks(project_id)
        total_overdue_tasks = self.get_total_overdue_tasks(project_id)
        total_resolved_issues = self.get_total_resolved_issues(project_id)
        total_unresolved_issues = self.get_total_unresolved_issues(project_id)
        overdue_tasks = self.get_overdue_tasks(project_id)
        pending_issues = self.get_pending_issues(project_id)
        project_messages = self.get_project_messages(project_id)
        user_activity_timeline = self.get_user_activity_timeline(project_id)
        chart_employee_timesheet = self.get_chart_employee_timesheet(project_id)
        chart_employee_tasks = self.get_chart_employee_tasks(project_id)
        chart_employee_issues = self.get_chart_employee_issues(project_id)
        
        return {
            'total_clients':total_clients,
            'total_employees':total_employees,
            'total_projects':total_projects,
            'total_paid_invoice':total_paid_invoice,
            'total_hour_logged':total_hour_logged,
            'total_pending_tasks':total_pending_tasks,
            'total_complete_tasks':total_complete_tasks,
            'total_overdue_tasks':total_overdue_tasks,
            'total_resolved_issues':total_resolved_issues,
            'total_unresolved_issues':total_unresolved_issues,
            'overdue_tasks':overdue_tasks,
            'pending_issues':pending_issues,
            'project_messages':project_messages,
            'user_activity_timeline':user_activity_timeline,
            'chart_employee_timesheet':chart_employee_timesheet,
            'chart_employee_tasks':chart_employee_tasks,
            'chart_employee_issues':chart_employee_issues,
        }
    
    @api.model
    def get_total_clients(self,project_id):
        self.env.cr.execute("select count(distinct project_project.partner_id) FROM project_project join account_analytic_account on account_analytic_account.id = analytic_account_id")
        result  =  self.env.cr.fetchone()
        return result
    
    @api.model
    def get_total_employees(self,project_id):
        group = self.env.ref('project.group_project_user')
        return len(group.users)
    
    @api.model
    def get_total_projects(self,project_id):
        projects = self.env['project.project'].search_count([])
        return projects
    
    @api.model
    def get_total_paid_invoice(self,project_id):
        invoices = self.env['account.invoice'].search_count([('type','in',('out_invoice', 'out_refund')),('state','=','paid')])
        return invoices
    
    @api.model
    def get_total_hour_logged(self,project_id):
        project_id = int(project_id)
        domain = [] if project_id == -1 else [('project_id','=',project_id)]
        timesheets = sum(timesheet.unit_amount for timesheet in self.env['account.analytic.line'].search(domain))
        return timesheets
    
    @api.model
    def get_total_pending_tasks(self,project_id):
        done_stage = self.env.ref('dashboard_projects.project_stage_2')
        cancelled_stage = self.env.ref('dashboard_projects.project_stage_3')
        
        project_id = int(project_id)
        domain = [('stage_id','!=',done_stage.id),('stage_id','!=',cancelled_stage.id)] if project_id == -1 else [('stage_id','!=',done_stage.id),('stage_id','!=',cancelled_stage.id),('project_id','=',project_id)]
        
        tasks = self.env['project.task'].search_count(domain)
        return tasks
    
    @api.model
    def get_total_complete_tasks(self,project_id):
        done_stage = self.env.ref('dashboard_projects.project_stage_2')
        
        project_id = int(project_id)
        domain = [('stage_id','=',done_stage.id)] if project_id == -1 else [('stage_id','=',done_stage.id),('project_id','=',project_id)]
        
        tasks = self.env['project.task'].search_count(domain)
        return tasks
    
    @api.model
    def get_total_overdue_tasks(self,project_id):
        cancelled_stage = self.env.ref('dashboard_projects.project_stage_3')
        project_id = int(project_id)
        domain = [('date_deadline','<',fields.Datetime.now()),('stage_id','!=',cancelled_stage.id)] if project_id == -1 else [('date_deadline','<',fields.Datetime.now()),('project_id','=',project_id),('stage_id','!=',cancelled_stage.id)]
        
        tasks = self.env['project.task'].search_count(domain)
        return tasks
    
    @api.model
    def get_overdue_tasks(self,project_id):
        
        project_id = int(project_id)
        domain = [('date_deadline','<',fields.Datetime.now())] if project_id == -1 else [('date_deadline','<',fields.Datetime.now()),('project_id','=',project_id)]
       
        
        tasks = self.env['project.task'].search_read(domain,['id','name','date_deadline','project_id'])
        return tasks
    
    @api.model
    def get_total_resolved_issues(self,project_id):
        # done_stage = self.env.ref('project.project_stage_2')
        #
        # project_id = int(project_id)
        # domain = [('stage_id','=',done_stage.id)] if project_id == -1 else [('stage_id','=',done_stage.id),('project_id','=',project_id)]
        #
        #
        # issues = self.env['project.issue'].search_count(domain)
        return []
    
    @api.model
    def get_total_unresolved_issues(self,project_id):
        # done_stage = self.env.ref('project.project_stage_2')
        # cancelled_stage = self.env.ref('project.project_stage_3')
        #
        # project_id = int(project_id)
        # domain = [('stage_id','!=',done_stage.id),('stage_id','!=',cancelled_stage.id)] if project_id == -1 else [('stage_id','!=',done_stage.id),('stage_id','!=',cancelled_stage.id),('project_id','=',project_id)]
        #
        #
        # issues = self.env['project.issue'].search_count(domain)
        return []
    
    @api.model
    def get_pending_issues(self,project_id):
        # done_stage = self.env.ref('project.project_stage_2')
        # cancelled_stage = self.env.ref('project.project_stage_3')
        #
        #
        # project_id = int(project_id)
        # domain = [('stage_id','!=',done_stage.id),('stage_id','!=',cancelled_stage.id)] if project_id == -1 else [('stage_id','!=',done_stage.id),('stage_id','!=',cancelled_stage.id),('project_id','=',project_id)]
        #
        #
        # issues = self.env['project.issue'].search_read(domain,['id','name','project_id'])
        return []

    @api.model
    def get_project_messages(self,project_id):
        project_id = int(project_id)
        
        #messages = self.env['mail.message'].search_read([('model','in',('project.issue','project.task')),('body','!=','')],['res_id','model','body','date'],limit = 30,order="id desc")
        messages = self.env['mail.message'].search_read([('model', '=', 'project.task'), ('body', '!=', '')],['res_id', 'model', 'body', 'date'], limit=30, order="id desc")
        data = []
        for message in messages:
            now_utc = datetime.utcnow()
            record_date_utc = message['date']
            d = now_utc - record_date_utc
            hours = d.seconds / 3600
            if d.days == 0 and hours < 1 :
                date = 'from ' + str(d.seconds/60) + ' minutes ago'
            elif d.days == 0 and hours < 24 :
                date = 'from ' + str(hours) + ' hours ago'
            else:
                date = 'from ' + str(d.days) + ' days ago'
            
            project_data = self.env[message['model']].browse(message['res_id'])
            if project_id == -1 or project_data.project_id.id == project_id:
                data.append({
                    'body': message['body'],
                    'date': str(date),
                    'project': project_data.project_id.name if project_data.project_id else '' + ' | ' + project_data.name if project_data else '',
                })
        return data
    
    
    @api.model
    def get_user_activity_timeline(self,project_id):
        #messages = self.env['mail.message'].search_read([('body','!=',''),('model','in',('project.task','project.issue'))],['res_id','model','create_uid','body','date'],limit = 30,order="id desc")
        messages = self.env['mail.message'].search_read([('body', '!=', ''), ('model', '=', 'project.task')],['res_id', 'model', 'create_uid', 'body', 'date'], limit=30, order="id desc")
        data = []
        for message in messages:
            now_utc = datetime.utcnow()
            record_date_utc = message['date']
            d = now_utc - record_date_utc
            hours = d.seconds / 3600
            if d.days == 0 and hours < 1 :
                date = 'from ' + str(d.seconds/60) + ' minutes ago'
            elif d.days == 0 and hours < 24 :
                date = 'from ' + str(hours) + ' hours ago'
            else:
                date = 'from ' + str(d.days) + ' days ago'
            
            user = self.env['res.users'].browse(message['create_uid'][0])
            
            data.append({
                'user_name':user.name,
                'user_image':'/web/image?model=res.users&field=image_small&id=' + str(user.id),
                'body': message['body'],
                'date': str(date),
                'project': self.env[message['model']].browse(message['res_id']).name,
            })
        return data
    
    @api.model
    def get_chart_employee_issues(self,project_id):
        # done_stage = self.env.ref('project.project_stage_2')
        # cancelled_stage = self.env.ref('project.project_stage_3')
        #
        # project_id = int(project_id)
        # domain = [('stage_id','!=',cancelled_stage.id)] if project_id == -1 else [('stage_id','!=',cancelled_stage.id),('project_id','=',project_id)]
        #
        #
        # users = []
        # resolved = []
        # unresolved = []
        # issues = self.env['project.issue'].search_read(domain,['user_id','stage_id'])
        # for issue in issues:
        #     if issue['user_id'] not in users:
        #         users.append(issue['user_id'])
        #
        # for user in users:
        #     resolved_val = 0
        #     unresolved_val = 0
        #     for issue in issues:
        #         user_issue_id = issue['user_id'][0] if issue['user_id'] else False
        #         current_user = user[0] if user else False
        #         if issue['stage_id'][0] == done_stage.id and user_issue_id == current_user:
        #             resolved_val +=1
        #         elif user_issue_id ==current_user:
        #             unresolved_val +=1
        #     resolved.append(resolved_val)
        #     unresolved.append(unresolved_val)
        
        return {
            'employee':[],
            'resolved':[],
            'unresolved':[]
        }
    
    @api.model
    def get_chart_project_issues(self,project_id):
        # done_stage = self.env.ref('project.project_stage_2')
        # cancelled_stage = self.env.ref('project.project_stage_3')
        #
        # project_id = int(project_id)
        # domain = [('stage_id','!=',cancelled_stage.id)] if project_id == -1 else [('stage_id','!=',cancelled_stage.id),('project_id','=',project_id)]
        #
        #
        # projects = []
        # resolved = []
        # unresolved = []
        # issues = self.env['project.issue'].search_read(domain,['stage_id','project_id'])
        # for issue in issues:
        #     if issue['project_id'] not in projects:
        #         projects.append(issue['project_id'])
        #
        # for project in projects:
        #     resolved_val = 0
        #     unresolved_val = 0
        #     for issue in issues:
        #         project_issue_id = issue['project_id'][0] if issue['project_id'] else False
        #         current_project = project[0] if project else False
        #         if issue['stage_id'][0] == done_stage.id and project_issue_id == current_project:
        #             resolved_val +=1
        #         elif project_issue_id == current_project:
        #             unresolved_val +=1
        #     resolved.append(resolved_val)
        #     unresolved.append(unresolved_val)
        
        return {
            'employee':[],
            'resolved':[],
            'unresolved':[]
        }
    
    @api.model
    def get_chart_employee_timesheet(self,project_id):
        project_id = int(project_id)
        domain = [] if project_id == -1 else [('project_id','=',project_id)]
        timesheets = self.env['account.analytic.line'].search(domain)
        
        users = []
        timesheet_data = []
        for timesheet in timesheets:
            if timesheet.user_id not in users:
                users.append(timesheet.user_id)
        
        for user in users:
            timesheet_val = 0
            for timesheet in timesheets:
                if timesheet.user_id.id == user.id:
                    timesheet_val += timesheet['unit_amount']
                    
            timesheet_data.append(timesheet_val)
            
        return {
            'employee':[user.name for user in users],
            'timesheet':timesheet_data,
        }
    
    @api.model
    def get_chart_project_timesheet(self,project_id):
        project_id = int(project_id)
        domain = [] if project_id == -1 else [('project_id','=',project_id)]
        timesheets = self.env['account.analytic.line'].search(domain)
        
        projects = []
        timesheet_data = []
        for timesheet in timesheets:
            if timesheet.project_id not in projects:
                projects.append(timesheet.project_id)
        
        for project in projects:
            timesheet_val = 0
            for timesheet in timesheets:
                if timesheet.project_id.id == project.id:
                    timesheet_val += timesheet['unit_amount']
                    
            timesheet_data.append(timesheet_val)
            
        return {
            'employee':[project.name for project in projects],
            'timesheet':timesheet_data,
        }
    
    @api.model
    def get_chart_employee_tasks(self,project_id):
        done_stage = self.env.ref('dashboard_projects.project_stage_2')
        cancelled_stage = self.env.ref('dashboard_projects.project_stage_3')
        
        project_id = int(project_id)
        domain = [('stage_id','!=',cancelled_stage.id)] if project_id == -1 else [('stage_id','!=',cancelled_stage.id),('project_id','=',project_id)]
        users = []
        resolved = []
        unresolved = []
        overdue = []
        tasks = self.env['project.task'].search_read(domain,['user_id','stage_id','date_deadline'])
        for task in tasks:
            if task['user_id'] not in users:
                users.append(task['user_id'])
        
        for user in users:
            resolved_val = 0
            unresolved_val = 0
            overdue_val = 0
            for task in tasks:
                user_task_id = task['user_id'][0] if task['user_id'] else False
                current_user = user[0] if user else False
                if task['stage_id'][0] == done_stage.id and user_task_id == current_user:
                    resolved_val +=1
                elif user_task_id == current_user:
                    unresolved_val +=1

                if task['date_deadline'] :
                    date_deadline = task['date_deadline']
                    date_now = datetime.now()
                    date_now = date_now.date()
                    if date_deadline < date_now and user_task_id == current_user:
                        overdue_val +=1
            resolved.append(resolved_val)
            unresolved.append(unresolved_val)
            overdue.append(overdue_val)
        
        return {
            'employee':[user[1] if user else 'Undefined' for user in users],
            'resolved':resolved,
            'unresolved':unresolved,
            'overdue':overdue
        }
    
    @api.model
    def get_chart_project_tasks(self,project_id):
        done_stage = self.env.ref('dashboard_projects.project_stage_2')
        cancelled_stage = self.env.ref('dashboard_projects.project_stage_3')
        
        project_id = int(project_id)
        domain = [('stage_id','!=',cancelled_stage.id)] if project_id == -1 else [('stage_id','!=',cancelled_stage.id),('project_id','=',project_id)]
       
        
        projects = []
        resolved = []
        unresolved = []
        overdue = []
        tasks = self.env['project.task'].search_read(domain,['date_deadline','stage_id','project_id'])
        for task in tasks:
            if task['project_id'] not in projects:
                projects.append(task['project_id'])
        
        for project in projects:
            resolved_val = 0
            unresolved_val = 0
            overdue_val = 0
            for task in tasks:
                project_task_id = task['project_id'][0] if task['project_id'] else False
                current_project = project[0] if project else False
                if task['stage_id'][0] == done_stage.id and project_task_id == current_project:
                    resolved_val +=1
                elif project_task_id ==current_project:
                    unresolved_val +=1
                if task['date_deadline'] :
                    date_deadline = task['date_deadline']
                    date_now = datetime.now()
                    date_now = date_now.date()
                    if date_deadline < date_now and project_task_id == current_project:
                        overdue_val +=1
            resolved.append(resolved_val)
            unresolved.append(unresolved_val)
            overdue.append(overdue_val)
        
        return {
            'employee':[project[1] if project else 'Undefined' for project in projects],
            'resolved':resolved,
            'unresolved':unresolved,
            'overdue':overdue
        }
    
    