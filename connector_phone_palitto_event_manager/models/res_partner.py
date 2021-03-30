import hashlib
import logging
import urllib

import requests

from odoo import _, api, models
from odoo.exceptions import UserError

from odoo.addons.web.controllers.main import clean_action

_logger = logging.getLogger(__name__)


class ResPartner(models.Model):
    _inherit = "res.partner"

    @api.multi
    def open_outgoing_notification(self):
        channel = "notify_info_%s" % self.env.user.id
        bus_message = {
            "message": _("Calling from : %s" % self.env.user.phone),
            "title": _("Outgoing Call to %s" % self.display_name),
            # 'sticky': True,
            "action_link_name": "action_link_name",
            "Outnotification": "OutGoingNotification",
            "id": self.id,
        }
        self.env["bus.bus"].sendone(channel, bus_message)

    @api.multi
    def outgoing_call_notification(self):
        # For Outgoing Calls
        if self == {}:
            raise UserError(_("Bad Partner Record"))
        if not self.env.user.company_id.server_address:
            raise UserError(_("Please specify server address in Company Setting"))
        server = self.env.user.company_id.server_address + "/DialNumber/?"
        number = self.phone  # Fetched from partner

        user = self.env.user
        ext = user.related_phone  # Fetched from user
        payload = {
            "ext": ext,
            "number": number,
        }
        payload = urllib.parse.urlencode(payload)
        url = server + payload
        _logger.info("URL ---- %s", url)
        response = requests.get(url=url, params={})
        # ToDo : This should be modified based on real response
        if response.status_code in (400, 401, 404, 500):
            error_msg = _(
                "Request Call failed with Status %s.\n\n"
                "Request:\nGET %s\n\n"
                "Response:\n%s"
            ) % (response.status_code, url or "", response.text)
            _logger.error(error_msg)

    @api.multi
    def incoming_call_notification(self):
        partners = self.ids
        action = self.env.ref(
            "connector_phone_palitto_event_manager.action_partners_tree_all"
        ).read()[0]
        if len(partners) > 1:
            action["domain"] = [("id", "in", partners)]
        elif partners:
            form_view = [(self.env.ref("base.view_partner_form").id, "form")]
            if "views" in action:
                action["views"] = form_view + [
                    (state, view) for state, view in action["views"] if view != "form"
                ]
            else:
                action["views"] = form_view
            action["res_id"] = partners[0]
        action = clean_action(action)
        return action
