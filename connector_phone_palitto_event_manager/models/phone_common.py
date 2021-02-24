import logging

from odoo import _, api, models

from odoo.addons.web.controllers.main import clean_action

_logger = logging.getLogger(__name__)


class PhoneCommon(models.AbstractModel):
    _inherit = "phone.common"

    @api.model
    def incall_notify_by_login(self, number, login_list):
        assert isinstance(login_list, list), "login_list must be a list"
        res = self.sudo().get_record_from_phone_number(number)
        users = self.env["res.users"].sudo().search([("login", "in", login_list)])
        action = self._prepare_incall_pop_action(res, number)
        action = clean_action(action)
        if action and res:
            for user in users:
                channel = "notify_info_%s" % user.id
                bus_message = {
                    "message": _("Incoming call from : " + res[2]),
                    "title": _("Incoming call"),
                    "action": action,
                    # 'sticky': True,
                    "action_link_name": "action_link_name",
                    "notification": "IncomingNotification",
                    "id": user.id,
                }
                self.sudo().env["bus.bus"].sendone(channel, bus_message)
                _logger.debug(
                    "This action has been sent to user ID %d: %s" % (user.id, action)
                )
        if res:
            callerid = res[2]
        else:
            callerid = False
        return callerid
