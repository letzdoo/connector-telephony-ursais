import hashlib
import logging
import urllib

import requests

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
    def open_outgoing_notification(self):
        #import pdb; pdb.set_trace()
        channel = "notify_info_%s" % self.env.user.id
        bus_message = {
            "message": _("Calling from : %s" % self.env.user.phone),
            "title": _("Outgoing Call to %s" % self.display_name),
            # 'sticky': True,
            "action_link_name": "action_link_name",
            "Outnotification": "OutGoingNotification",
            "id": self.id,
        }
        self.update_called_for_values()
        self.env["bus.bus"].sendone(channel, bus_message)

    @api.multi
    def outgoing_call_notification(self):
        # For Outgoing Calls
        #import pdb; pdb.set_trace()
        if self == {}:
            raise UserError(_("Bad Partner Record"))
        if not self.env.user.company_id.server_address:
            raise UserError(_("Please specify server address in Company Setting"))
        #server = self.env.user.company_id.server_address + "/DialNumber/?"
        server = self.env.user.company_id.server_address
        number = self.called_for_mobile and self.mobile or self.phone  # Fetched from partner

        user = self.env.user
        ext = user.related_phone  # Fetched from user
        #payload = {
        #    "ext": ext,
        #    "number": number,
        #}
        session_id = "60D94B51-176E-4866-ADD7-A9A9D8C30089"
        endpoint = "/v3/cca/sessions/" + session_id + "/dial?Content-Type=application/json&token=AKXxaFOFkQJ5Qj72P1BWys7c3Z1wlammAqELqj9xVeA="
        payload = {
            #"Content-Type": "application/json",
            #"token": "AKXxaFOFkQJ5Qj72P1BWys7c3Z1wlammAqELqj9xVeA=",
            "OrgPhoneNo": "4806244497",
            "DstPhoneNo": "9092822864",
            "CallingName":  self.display_name,
            "CallingNumber": "9092822864",
            "ExecutionAsync": True,
            "ReturnRecUrl": True            
        }


        payload = urllib.parse.urlencode(payload)
        url = server + endpoint + payload
        _logger.info("URL ---- %s", url)
        #response = requests.post(url=url, params={'Content-Type':'application/json','token': 'AKXxaFOFkQJ5Qj72P1BWys7c3Z1wlammAqELqj9xVeA='})
        response = requests.post(url=url, params={})
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
