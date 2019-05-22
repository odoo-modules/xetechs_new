odoo.define('project_task_run_stop.pause', function (require) {
    "use strict";

    let core = require('web.core');
    let Widget = require('web.Widget');
    let SystrayMenu = require('web.SystrayMenu');

    let channel = 'need_refresh_fast_timesheet';
    let _t = core._t;


    let ButtonPause = Widget.extend({
        template: 'project_task_run_stop.ButtonPause',
        events: {
            "click": "_onButtonPauseClick",
        },
        init: function () {
            this._super.apply(this, arguments);
            let self = this;
            self._rpc({
                model: 'account.analytic.line',
                method: 'init_fast_timesheet',
                args: [false],
            }).then(function (value) {
                if (value) {
                    self._set_timer(value);
                }
            });
        },
        start: function () {
            this._super.apply(this, arguments);
            this.call('bus_service', 'addChannel', channel);
            this.call('bus_service', 'startPolling');
            this.call('bus_service', 'onNotification', this, this._on_notification_stop_timesheet);
        },
        _onButtonPauseClick: function () {
            let self = this;
            self._rpc({
                model: 'account.analytic.line',
                method: 'start_stop_fast_timesheet',
                args: [false],
            }).then(function (value) {
                if (value) {
                    self._stop_timesheet();
                } else {
                    self._start_timesheet();
                }
            });
        },
        _start_timesheet: function () {
            let self = this;
            self._rpc({
                model: 'account.analytic.line',
                method: 'start_fast_timesheet',
                args: [false],
            }).then(function (res) {
                if (res) {
                    self._widget_start();
                } else {
                    alert(_t('First, install the default project in the settings'));
                }
            });
        },
        _widget_start: function () {
            this.timer = true;
            this._set_timer(0);
        },
        _stop_timesheet: function () {
            this.do_action({
                name: _t("Description of work"),
                type: 'ir.actions.act_window',
                res_model: 'project_task_run_stop.wizard_stop_fast_timesheet',
                views: [[false, 'form']],
                target: 'new',
            });
        },
        _on_notification_stop_timesheet: function (notifications) {
            let self = this;
            _.each(notifications, function (notification) {
                let ch = notification[0];
                if (ch === channel) {
                    self._widget_stop();
                }
            });
        },
        _widget_stop: function () {
            clearInterval(this.timer);
            this.$el.find('#fast_timesheet_timer').removeClass('ml4').removeClass('fa').html('');
            this.$el.find('#fast_timesheet_icon').removeClass('fa-stop').addClass('fa-play');
        },
        _set_timer: function (period) {
            let button = this.$el.find('#fast_timesheet_icon');
            button.removeClass('fa-play').addClass('fa-stop');
            let Timer = this.$el.find('#fast_timesheet_timer');
            Timer.addClass('ml4').addClass('fa');
            if (period < 0) {
                period = 0;
            }
            let hours = Math.floor(period / 3600);
            let mins = Math.floor((period - hours * 3600) / 60);
            let seconds = Math.floor(period - hours * 3600 - mins * 60);
            let hours_v = 0;
            let mins_v = 0;
            let seconds_v = 0;

            this.timer = setInterval(function () {
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
        },

    });

    SystrayMenu.Items.push(ButtonPause);

});  