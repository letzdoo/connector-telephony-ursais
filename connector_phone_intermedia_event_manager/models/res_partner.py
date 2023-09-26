import hashlib
import logging
import urllib

import requests

from odoo import _, api, fields, models
from odoo.exceptions import UserError

from odoo.addons.web.controllers.main import clean_action

_logger = logging.getLogger(__name__)

headers = {"content-type": "application/json", "token":"AKXxaFOFkQJ5Qj72P1BWys7c3Z1wlammAqELqj9xVeA=", 'Accept': 'text/plain'}

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
    def _get_intermedia_credentials(self):
        company_id = self.env.user.company_id
        if not company_id.intermedia_server_address or \
            not company_id.intermedia_token:
            raise UserError(_("Please configure intermedia URL and Token in Company Setting"))
        return {'server_address': company_id.intermedia_server_address,
                'token':company_id.intermedia_token
        }

    @api.multi
    def _check_agent_status(self, user=False):
        """ Check Agent Status via registered AgentID"""
        credentials = self._get_intermedia_credentials()
        if not user:
            user = self.env.user
        if not user.intermedia_agentid:
            raise UserError(_("Please configure intermedia AgentID on User"))
        url = credentials['server_address'] + "/agents/" + user.intermedia_agentid
        _logger.info("Agent Status URL ---- %s", url)
        response = requests.get(url=url, headers=headers, params={})
        if response.status_code == 200 and response.json().get("IsActive", False):
            return True
        elif response.status_code in (400, 401, 404, 500):
            error_msg = _(
                "Request Call failed with Status %s.\n\n"
                "Request:\nGET %s\n\n"
                "Response:\n%s"
            ) % (response.status_code, url or "", response.text)
            _logger.error(error_msg)
            return False
        else:
            return False

    @api.multi
    def _check_cca_agent_session(self):
        """ Check Agent Session details via registered AgentID"""
        credentials = self._get_intermedia_credentials()
        if not (self.env.user.intermedia_agentid and self._check_agent_status()):
            raise UserError(_("Please configure Intermedia AgentId on User and Contact Center."))
        url = credentials['server_address'] + "/cca/sessions"
        _logger.info("Agent Status URL ---- %s", url)
        response = requests.get(url=url, headers=headers, params={})
        if response.status_code == 200:
            for res in response.json():
                if str(res.get("AgentId", "")) == self.env.user.intermedia_agentid:
                    return res.get("SessionId")
            raise UserError("Agent’s Session ID is not valid. Please login to Contact Center to activate")
        elif response.status_code in (400, 401, 404, 500):
            error_msg = _(
                "Request Call failed with Status %s.\n\n"
                "Request:\nGET %s\n\n"
                "Response:\n%s"
            ) % (response.status_code, url or "", response.text)
            _logger.error(error_msg)
            return False
        else:
            return False

    @api.multi
    def intermedia_open_outgoing_notification(self):
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
    def intermedia_outgoing_call_notification(self):
        # For Outgoing Calls
        if self == {}:
            raise UserError(_("Bad Partner Record"))
        session_id = self._check_cca_agent_session()
        if session_id:
            credentials = self._get_intermedia_credentials()
            url = credentials['server_address'] + "/cca/sessions/" + session_id + "/dial"
            number = self.called_for_mobile and self.mobile or self.phone  # Fetched from partner
    
            # Dial request parameters
    
            payload = {
                  "OrgPhoneNo": self.env.user.intermedia_agent_phone,
                  "DstPhoneNo": number,
                  "CallingName": self.name,
                  "CallingNumber": self.env.user.intermedia_agent_phone,
                  "ExecutionAsync": True,
                  "ReturnRecUrl": True
                }
            _logger.info("URL ---- %s", url)
            response = requests.request("POST",url,json=payload, headers=headers)
            print ("=======response========", response, response.text, response.content)
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
            "connector_phone_intermedia_event_manager.intermedia_action_partners_tree_all"
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
