odoo.define("connector_phone_cloudcti_event_manager.notification_widget", function(require) {
        "use strict";

    const Notification = require('web.Notification')
    const session = require('web.session')

    Notification.include({

        willStart: function () {
            var self = this;
            var gettime = this._rpc({
                model: 'res.company',
                method: 'get_popup_time',
                args: [[session.company_id]],
            }).then(function (time) {
                self._autoCloseDelay = time && time * 1000 || 2500
            });
            return $.when(
                gettime,
                this._super.apply(this, arguments)
            );
        },
    });
});
