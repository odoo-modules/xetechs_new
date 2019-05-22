odoo.define('project_task_run_stop.auto_refresh_project_tasks', function (require) {
    "use strict";

    let WebClient = require('web.WebClient');
    let channel = 'need_refresh_tasks';

    let ptrs_delay = (function () {
        let timer = 0;
        return function (callback, ms) {
            clearTimeout(timer);
            timer = setTimeout(callback, ms);
        };
    })();

    WebClient.include({
        start: function () {
            this._super.apply(this, arguments);
            this.call('bus_service', 'addChannel', channel);
            this.call('bus_service', 'startPolling');
            this.call('bus_service', 'onNotification', this, this.on_notification_ptrs);
        },
        on_notification_ptrs: function (notifications) {
            let self = this;
            _.each(notifications, function (notification) {
                let ch = notification[0];
                let msg = notification[1];
                if (ch === channel) {
                    self.handler_msg_ptrs(msg);
                }
            });
        },
        handler_msg_ptrs: function (msg) {
            let action = this.action_manager.getCurrentAction();
            let controller = this.action_manager.getCurrentController();
            if (action && controller) {
                if (controller.widget.modelName === msg.model && controller.widget.mode === "readonly") {
                    this._reload(controller);
                }
            }
        },
        _reload: function (controller) {
            ptrs_delay(function () {
                controller.widget.reload();
            }, 1000);
        },
    });

});
