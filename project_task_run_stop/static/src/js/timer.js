odoo.define('project_task_run_stop.timer', function (require) {
    "use strict";

    let KanbanRecord = require('web.KanbanRecord');
    let FormRenderer = require('web.FormRenderer');


    KanbanRecord.include({
        _render: function () {
            return $.when(this._super.apply(this, arguments), this._render_run_timer());
        },
        _render_run_timer: function () {
            if (this.modelName === 'project.task' && this.recordData.task_run) {

                let Timer = this.$el.find('#timer');
                Timer.attr('title', 'Started by ' + this.recordData.task_run_user.data.display_name);
                let now = new Date();
                let period = 0;
                if (this.recordData.task_pause_last_time) {
                    period = ((now.getTime() - this.recordData.task_pause_last_time) / 1000) + (this.recordData.task_run_sum * 3600);
                } else {
                    period = (now.getTime() - this.recordData.task_run_time) / 1000;
                }
                if (period < 0) {
                    period = 0;
                }
                let hours = Math.floor(period / 3600);
                let mins = Math.floor((period - hours * 3600) / 60);
                let seconds = Math.floor(period - hours * 3600 - mins * 60);
                let hours_v = 0;
                let mins_v = 0;
                let seconds_v = 0;

                if (this.recordData.task_pause) {
                    let period = this.recordData.task_run_sum * 3600;
                    let hours = Math.floor(period / 3600);
                    let mins = Math.floor((period - hours * 3600) / 60);
                    let seconds = Math.floor(period - hours * 3600 - mins * 60);
                    if (hours < 10) {
                        hours = '0' + hours;
                    }
                    if (mins < 10) {
                        mins = '0' + mins;
                    }
                    if (seconds < 10) {
                        seconds = '0' + seconds;
                    }
                    Timer.html(hours + ':' + mins);
                    return;
                }

                setInterval(function () {
                    seconds++;
                    if (seconds > 59) {
                        seconds = 0;
                        mins++;
                    }
                    if (mins > 59) {
                        mins = 0;
                        hours++;
                    }

                    if (hours < 10) {
                        hours_v = '0' + hours;
                    } else {
                        hours_v = hours;
                    }
                    if (mins < 10) {
                        mins_v = '0' + mins;
                    } else {
                        mins_v = mins;
                    }
                    if (seconds < 10) {
                        seconds_v = '0' + seconds;
                    } else {
                        seconds_v = seconds;
                    }

                    if (seconds_v % 2 === 0) {
                        Timer.html(hours_v + ':' + mins_v);
                    } else {
                        Timer.html(hours_v + ' ' + mins_v);
                    }
                }, 1000);
            }
        },

    });


    FormRenderer.include({
        _renderHeaderButtons: function (node) {
            let $buttons = this._super(node);
            let fields_data = this.state.data;
            if (this.state.model === 'project.task' && fields_data.task_run) {

                $buttons.append('<div id="timer" class="my-auto text-danger font-weight-bold ml16 h4" title = "Started by ' + fields_data.task_run_user.data.display_name + '"/>');
                let Timer = $buttons.find('#timer');
                let now = new Date();
                let period = 0;
                if (fields_data.task_pause_last_time) {
                    period = ((now.getTime() - fields_data.task_pause_last_time) / 1000) + (fields_data.task_run_sum * 3600);
                } else {
                    period = (now.getTime() - fields_data.task_run_time) / 1000;
                }
                if (period < 0) {
                    period = 0;
                }
                let hours = Math.floor(period / 3600);
                let mins = Math.floor((period - hours * 3600) / 60);
                let seconds = Math.floor(period - hours * 3600 - mins * 60);
                let hours_v = 0;
                let mins_v = 0;
                let seconds_v = 0;

                if (fields_data.task_pause) {
                    let period = fields_data.task_run_sum * 3600;
                    let hours = Math.floor(period / 3600);
                    let mins = Math.floor((period - hours * 3600) / 60);
                    let seconds = Math.floor(period - hours * 3600 - mins * 60);
                    if (hours < 10) {
                        hours = '0' + hours;
                    }
                    if (mins < 10) {
                        mins = '0' + mins;
                    }
                    if (seconds < 10) {
                        seconds = '0' + seconds;
                    }
                    Timer.html(hours + ':' + mins);
                    return $buttons;
                }

                setInterval(function () {
                    seconds++;
                    if (seconds > 59) {
                        seconds = 0;
                        mins++;
                    }
                    if (mins > 59) {
                        mins = 0;
                        hours++;
                    }

                    if (hours < 10) {
                        hours_v = '0' + hours;
                    } else {
                        hours_v = hours;
                    }
                    if (mins < 10) {
                        mins_v = '0' + mins;
                    } else {
                        mins_v = mins;
                    }
                    if (seconds < 10) {
                        seconds_v = '0' + seconds;
                    } else {
                        seconds_v = seconds;
                    }

                    if (seconds_v % 2 === 0) {
                        Timer.html(hours_v + ':' + mins_v);
                    } else {
                        Timer.html(hours_v + ' ' + mins_v);
                    }
                }, 1000);
            }
            return $buttons;
        },

    });

});