odoo.define("dashboard_projects.project_management_dashboard", function(require) {
    "use strict";
     
    var core = require("web.core");
    var dataset = require("web.data");
    var AbstractAction = require('web.AbstractAction');
    var _t = core._t;
    var QWeb = core.qweb;
    
    var project_dashboard = AbstractAction.extend({
        template: 'Prjects_dashboard',
        events:{
            'change #projects_selectbox': 'projects_selectbox_onchange',
            'click #get_chart_employee_timesheet':'get_chart_employee_timesheet',
            'click #get_chart_project_timesheet':'get_chart_project_timesheet',
            'click #get_chart_employee_task' : 'get_chart_employee_task',
            'click #get_chart_project_task' : 'get_chart_project_task',
            'click #get_chart_employee_issue' : 'get_chart_employee_issue',
            'click #get_chart_project_issue' : 'get_chart_project_issue',
        },
        //Filter by project
        projects_selectbox_onchange:function(e){
            var self = this;
            var current_val = $(e.currentTarget).val();
            if (current_val == -1) {
                $(".first-client-block").show();
                $(".user-activities-timeline").show();
            }else{
                $(".first-client-block").hide();
                $(".user-activities-timeline").hide();
            }
            self.fetchblocks(current_val);
        },
        
        //Timesheet charts
        get_chart_employee_timesheet:function(e){
            var self = this;
            var current_val = $(e.currentTarget).val();
            $(".chart-timesheet-link").removeClass('active');
            $(e.currentTarget).addClass('active');
            var project_id = $("#projects_selectbox").val();
            var crm_dashboard = this._rpc({
                model:'project.management.dashboard',
                method: 'get_chart_employee_timesheet',
                args: [project_id],
            }).then(function(data){
                self.drawChart_employee_timesheet(data,'User / Timesheet');
            });
        },
        get_chart_project_timesheet:function(e){
            var self = this;
            var current_val = $(e.currentTarget).val();
            $(".chart-timesheet-link").removeClass('active');
            $(e.currentTarget).addClass('active');
            var project_id = $("#projects_selectbox").val();
            
            var crm_dashboard = this._rpc({
                model:'project.management.dashboard',
                method: 'get_chart_project_timesheet',
                args: [project_id],
            }).then(function(data){
                self.drawChart_employee_timesheet(data,'Project / Timesheet');
            });
        },
        
        //Tasks charts
        get_chart_employee_task:function(e){
            var self = this;
            var current_val = $(e.currentTarget).val();
            $(".chart-tasks-link").removeClass('active');
            $(e.currentTarget).addClass('active');
            var project_id = $("#projects_selectbox").val();
            
            var crm_dashboard = this._rpc({
                model:'project.management.dashboard',
                method: 'get_chart_employee_tasks',
                args: [project_id],
            }).then(function(data){
                self.drawChart_employee_task(data,'Employee / Task');
            });
        },
        get_chart_project_task:function(e){
            var self = this;
            var current_val = $(e.currentTarget).val();
            $(".chart-tasks-link").removeClass('active');
            $(e.currentTarget).addClass('active');
            var project_id = $("#projects_selectbox").val();
            
            var crm_dashboard = this._rpc({
                model:'project.management.dashboard',
                method: 'get_chart_project_tasks',
                args: [project_id],
            }).then(function(data){
                self.drawChart_employee_task(data,'Project / Task');
            });
        },
        //Issues charts
        get_chart_employee_issue:function(e){
            var self = this;
            var current_val = $(e.currentTarget).val();
            $(".chart-issues-link").removeClass('active');
            $(e.currentTarget).addClass('active');
            var project_id = $("#projects_selectbox").val();
            var crm_dashboard = this._rpc({
                model:'project.management.dashboard',
                method: 'get_chart_employee_issues',
                args: [project_id],
            }).then(function(chart_employee_issues){
                self.drawChart_employee_issue(chart_employee_issues,'Employee / Issue');
            });
        },
        get_chart_project_issue:function(e){
            var self = this;
            var current_val = $(e.currentTarget).val();
            $(".chart-issues-link").removeClass('active');
            $(e.currentTarget).addClass('active');
            var project_id = $("#projects_selectbox").val();
            
            var crm_dashboard = this._rpc({
                model:'project.management.dashboard',
                method: 'get_chart_project_issues',
                args: [project_id],
            }).then(function(chart_project_issues){
                self.drawChart_employee_issue(chart_project_issues,'Project / Issue');
            });
        },
        start: function(){
            var self = this;
            var crm_dashboard = this._rpc({
                model:'project.management.dashboard',
                method: 'get_all_projects',
                args: [],
            }).done(function(projects){
                _.each(projects,function(project){
                    $('.projects-container select').append('<option value="' + project.id + '">'+ project.name  +'</option>') 
                });
            });
            self.fetchblocks(-1)
        },
        fetchblocks : function(project_id){
            var self = this;
            $(".chart-timesheet-link").removeClass('active');
            $(".chart-issues-link").removeClass('active');
            $(".chart-tasks-link").removeClass('active');
            $(".chart-timesheet-link-1").addClass('active');
            $(".chart-issues-link-1").addClass('active');
            $(".chart-tasks-link-1").addClass('active');
            var crm_dashboard = this._rpc({
                model:'project.management.dashboard',
                method: 'get_projects_dashboard_data',
                args: [project_id],
            }).then(function(projects){
                $(".total_clients").html(projects.total_clients);
                $(".total_employees").html(projects.total_employees);
                $(".total_projects").html(projects.total_projects);
                $(".total_paid_invoice").html(projects.total_paid_invoice);
                $(".total_hour_logged").html(parseFloat((projects.total_hour_logged.toFixed(2))));
                $(".total_pending_tasks").html(projects.total_pending_tasks);
                $(".total_complete_tasks").html(projects.total_complete_tasks);
                $(".total_overdue_tasks").html(projects.total_overdue_tasks);
                $(".total_resolved_issues").html(projects.total_resolved_issues);
                $(".total_unresolved_issues").html(projects.total_unresolved_issues);
                $(".overdue-tasks-container").html(QWeb.render("overdue_tasks_template",{overdue_tasks: projects.overdue_tasks}));
                $(".pending-issue-container").html(QWeb.render("pending_issue_template",{pending_issues: projects.pending_issues}));
                $(".project-time-activity-container").html(QWeb.render("project_time_activity",{project_messages: projects.project_messages}));
                $(".user-activity-timeline-container").html(QWeb.render("user_activity_timeline",{user_activity_timeline: projects.user_activity_timeline}));
                self.drawChart_employee_timesheet(projects.chart_employee_timesheet,'Employee / Timesheet');
                self.drawChart_employee_task(projects.chart_employee_tasks,'Employee / Task');
                self.drawChart_employee_issue(projects.chart_employee_issues,'Employee / Issue');
            });
        },
        drawChart_employee_timesheet: function(projects,title){
            var chart = Highcharts.chart('chart_timesheet', {
                chart: {
                    type: 'column'
                },
            
                title: {
                    text: ''
                },
            
                legend: {
                    align: 'right',
                    verticalAlign: 'middle',
                    layout: 'vertical'
                },
            
                xAxis: {
                    categories: projects.employee,
                },
            
                yAxis: {
                    title: {
                        text: 'Hours'
                    }
                },
            
                series: [{
                    name: 'Total hours logged',
                    data: projects.timesheet
                }],
            
                responsive: {
                    rules: [{
                        condition: {
                            maxWidth: 500
                        },
                        chartOptions: {
                            legend: {
                                align: 'center',
                                verticalAlign: 'bottom',
                                layout: 'horizontal'
                            },
                            yAxis: {
                                labels: {
                                    align: 'left',
                                    x: 0,
                                    y: -5
                                },
                                title: {
                                    text: null
                                }
                            },
                            subtitle: {
                                text: null
                            },
                            credits: {
                                enabled: false
                            }
                        }
                    }]
                }
            });
        },
        drawChart_employee_task : function(projects,title){
            var chart = Highcharts.chart('chart_employee_tasks', {
                chart: {
                    type: 'column'
                },
            
                title: {
                    text: ''
                },
            
                legend: {
                    align: 'right',
                    verticalAlign: 'middle',
                    layout: 'vertical'
                },
            
                xAxis: {
                    categories: projects.employee,
                },
            
                yAxis: {
                    title: {
                        text: 'Number of issues'
                    }
                },
            
                series: [{
                    name: 'Resloved',
                    data: projects.resolved
                }, {
                    name: 'Overdue',
                    data: projects.overdue,
                    color:'#ff0000'
                }, {
                    name: 'Unresolved',
                    data: projects.unresolved
                }],
            
                responsive: {
                    rules: [{
                        condition: {
                            maxWidth: 500
                        },
                        chartOptions: {
                            legend: {
                                align: 'center',
                                verticalAlign: 'bottom',
                                layout: 'horizontal'
                            },
                            yAxis: {
                                labels: {
                                    align: 'left',
                                    x: 0,
                                    y: -5
                                },
                                title: {
                                    text: null
                                }
                            },
                            subtitle: {
                                text: null
                            },
                            credits: {
                                enabled: false
                            }
                        }
                    }]
                }
            });
        },
        drawChart_employee_issue : function(projects,title){
            var chart = Highcharts.chart('chart_employee_issues', {
                chart: {
                    type: 'column'
                },
            
                title: {
                    text: ''
                },
            
                legend: {
                    align: 'right',
                    verticalAlign: 'middle',
                    layout: 'vertical'
                },
            
                xAxis: {
                    categories: projects.employee,
                },
            
                yAxis: {
                    title: {
                        text: 'Number of issues'
                    }
                },
            
                series: [{
                    name: 'Resloved',
                    data: projects.resolved
                }, {
                    name: 'Unresolved',
                    data: projects.unresolved
                }],
            
                responsive: {
                    rules: [{
                        condition: {
                            maxWidth: 500
                        },
                        chartOptions: {
                            legend: {
                                align: 'center',
                                verticalAlign: 'bottom',
                                layout: 'horizontal'
                            },
                            yAxis: {
                                labels: {
                                    align: 'left',
                                    x: 0,
                                    y: -5
                                },
                                title: {
                                    text: null
                                }
                            },
                            subtitle: {
                                text: null
                            },
                            credits: {
                                enabled: false
                            }
                        }
                    }]
                }
            });
        },
    });
    core.action_registry.add("dashboard_projects.dashboard", project_dashboard);
});
