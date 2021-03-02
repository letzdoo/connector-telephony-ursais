import logging

from odoo import _, api, models

from odoo.addons.web.controllers.main import clean_action

_logger = logging.getLogger(__name__)


class PhoneCommon(models.AbstractModel):
    _inherit = "phone.common"

    def get_record_from_phone_number(self, presented_number):
        _logger.debug(
            "Call get_name_from_phone_number with number = %s" % presented_number
        )
        if not isinstance(presented_number, str):
            _logger.warning(
                "Number '%s' should be a 'str' but it is a '%s'"
                % (presented_number, type(presented_number))
            )
            return False
        if not presented_number.isdigit():
            _logger.warning(
                "Number '%s' should only contain digits." % presented_number
            )

        nr_digits_to_match_from_end = (
            self.env.user.company_id.number_of_digits_to_match_from_end
        )
        if len(presented_number) >= nr_digits_to_match_from_end:
            end_number_to_match = presented_number[
                -nr_digits_to_match_from_end : len(presented_number)
            ]
        else:
            end_number_to_match = presented_number
        partner = self.env["res.partner"].sudo().search(
            [
                "|",
                ("phone", "=", end_number_to_match),
                ("mobile", "=", end_number_to_match),
            ],
            limit=1,
        )
        return ("res.partner", partner.id, partner.name)

    @api.model
    def incall_notify_by_login(self, number, login_list, calltype="Incoming Call"):
        assert isinstance(login_list, list), "login_list must be a list"
        res = self.sudo().get_record_from_phone_number(number)
        response = False
        if res:
            callerid = res[2]
            users = self.env["res.users"].sudo().search([("login", "in", login_list)])
            action = self._prepare_incall_pop_action(res, number)
            action = clean_action(action)
            if action:
                for user in users:
                    channel = "notify_info_%s" % user.id
                    bus_message = {
                        "message": _(calltype + " from : " + callerid),
                        "title": _(calltype),
                        "action": action,
                        "action_link_name": "action_link_name",
                        "notification": "IncomingNotification",
                        "id": res[1],
                    }
                    self.sudo().env["bus.bus"].sendone(channel, bus_message)
                    _logger.debug(
                        "This action has been sent to user ID %d: %s"
                        % (user.id, action)
                    )

            response = callerid
        return response
