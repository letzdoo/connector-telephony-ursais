import logging
import simplejson

import requests
from requests.auth import HTTPBasicAuth

from odoo import _, api, fields, models
from odoo.exceptions import UserError

from odoo.addons.web.controllers.main import clean_action

_logger = logging.getLogger(__name__)

class ResPartner(models.Model):
    _inherit = "res.partner"

    called_for_phone = fields.Boolean()
    called_for_mobile = fields.Boolean()

    def update_called_for_values(self):
        for partner in self:
            if self._context.get('phone_partner'):
                partner.called_for_phone = True
                partner.called_for_mobile = False
            elif self._context.get('mobile_partner'):
                partner.called_for_phone = False
                partner.called_for_mobile = True
            else:
                partner.called_for_phone = False
                partner.called_for_mobile = False

    @api.multi
    def _get_cloudcti_credentials(self):
        user = self.env.user
        company_id = user.company_id
        if not company_id.cloudcti_url or \
            not user.cloudcti_token:
            raise UserError(_("Please configure CloudCTI URL in Company Setting and Token in User"))
        return {'server_address': company_id.cloudcti_url,
                'token': user.cloudcti_token,
                'cloudcti_username': user.cloudcti_username,
                'cloudcti_password': user.cloudcti_password,
        }

    @api.multi
    def cloudcti_open_outgoing_notification(self):
        channel = "notify_info_%s" % self.env.user.id
        bus_message = {
            "message": _("Calling from : %s" % self.env.user.phone),
            "title": _("Outgoing Call to %s" % self.display_name),
            "action_link_name": "action_link_name",
            "Outnotification": "OutGoingNotification",
            "id": self.id,
        }
        self.update_called_for_values()
        self.env["bus.bus"].sendone(channel, bus_message)

    @api.multi
    def cloudcti_outgoing_call_notification(self):
        # For Outgoing Calls
        if self == {}:
            raise UserError(_("Bad Partner Record"))
        credentials = self._get_cloudcti_credentials()
        number = self.called_for_mobile and self.mobile or self.phone  # Fetched from partner
        url = credentials['server_address'] + "/makecall/" + number
        headers = {"content-type": "application/json"}
        response = requests.request(
            "GET",
            url,
            auth=HTTPBasicAuth(credentials.get("cloudcti_username"), credentials.get("cloudcti_password")),
            headers=headers
        )
        _logger.info("Response ---- %s", response.text)
        # ToDo : This should be modified based on real response
        if response.status_code in (400, 401, 403, 403, 500):
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
            "connector_phone_cloudcti_event_manager.cloudcti_action_partners_tree_all"
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
