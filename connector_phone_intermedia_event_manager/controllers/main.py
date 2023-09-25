from odoo import http
from odoo.http import request

import pytz

from datetime import datetime


class INTERMEDIAVOIP(http.Controller):

    def create_cdr_record(self, user, **kw):
        # if kw.get("CallType") == "inbound":
        #     call_type = "inbound"
        # else:
        #     inbound_flag = "outbound"
        return_date = self.convert_into_correct_timezone(kw.get("StartTime"), user)
        vals = {
            "guid": kw.get("GUID"),
            "inbound_flag": kw.get("CallType"),
            "call_start_time": return_date,
            "state": "offering",
            "called_id": kw.get("CalledID"),
        }
        return request.env["phone.cdr"].sudo().create(vals)

    def convert_into_correct_timezone(self, record_date, user):
        record_date = datetime.strptime(record_date, '%Y-%m-%d %H:%M:%S')
        timezone = request.env.context.get('tz', False) or user.partner_id.tz
        return_date = None
        if timezone:
            src_tz = pytz.timezone("UTC")
            dst_tz = pytz.timezone(timezone)
            return_date = dst_tz.localize(record_date).astimezone(src_tz)
        return return_date

    def _check_authentication(self, **kw):
        api_key = request.env['ir.config_parameter'].sudo().get_param('connector_phone_intermedia_event_manager.secret_key')
        if api_key != kw.get("secret_key"):
            return False
        else:
            return True

    @http.route(
        "/mycontactcenter/incomingCall", type="http", auth="public", website=True, sitemap=False
    )
    def intermedia_incoming_calls(self, *args, **kw):
        validation = self._check_authentication(**kw)
        if not validation:
            return {'message': 'Invalid API key.', 'status': 403,}
        user = (
            request.env["res.users"]
            .sudo()
            .search(
                [
                    ("intermedia_agentid", "=", kw.get("AgentId")),
                ],
                limit=1,
            )
        )
        if user:
            agent_status = user.partner_id._check_agent_status(user)
            if not agent_status:
                return ""
            cdr = self.create_cdr_record(user, **kw)
            if cdr and user:
                cdr.sudo().write({"user_id": user.id, "called_id_name": user.name})
                return (
                    request.env["phone.common"]
                    .sudo()
                    .incall_notify_by_login(
                        kw.get("CallerID"),
                        [user.login],
                        calltype="Incoming Call",
                    )
                )
            else:
                return ""
        else:
            return ""

    @http.route(
        "/mycontactcenter/outgoingCall", type="http", auth="public", website=True, sitemap=False
    )
    def intermedia_outgoing_calls(self, *args, **kw):
        validation = self._check_authentication(**kw)
        if not validation:
            return {'message': 'Invalid API key.', 'status': 403,}
        user = (
            request.env["res.users"]
            .sudo()
            .search(
                [
                    ("related_phone", "=", kw.get("AgentId")),
                ],
                limit=1,
            )
        )

        cdr = self.create_cdr_record(user, **kw)
        if cdr:
            partner = (
                request.env["phone.common"]
                .sudo()
                .get_record_from_phone_number(kw.get("CalledID"))
            )
            cdr_vals = {
                "caller_id": kw.get("AgentId"),
                "partner_ids": [(6, 0, partner.ids)],
                "state": "completed",
                "user_id": user.id,
            }
            cdr.sudo().write(cdr_vals)
            return ""
        else:
            return ""

    @http.route(
        "/mycontactcenter/missedCall", type="http", auth="public", website=True, sitemap=False
    )
    def intermedia_missedCall_calls(self, *args, **kw):
        validation = self._check_authentication(**kw)
        if not validation:
            return {'message': 'Invalid API key.', 'status': 403,}
        user = (
            request.env["res.users"]
            .sudo()
            .search(
                [
                    ("related_phone", "=", kw.get("AgentId")),
                ],
                limit=1,
            )
        )
        cdr = (
            request.env["phone.cdr"]
            .sudo()
            .search([("guid", "=", kw.get("GUID"))], limit=1)
        )

        if cdr:
            partner = (
                request.env["phone.common"]
                .sudo()
                .get_record_from_phone_number(kw.get("CallerID"))
            )
            return_date = self.convert_into_correct_timezone(kw.get("EndTime"), user)
            cdr_vals = {
                "call_end_time": return_date,
                "caller_id": kw.get("CallerID"),
                "partner_ids": [(6, 0, partner.ids)],
                "state": "missed",
                "user_id": user.id,
            }
            cdr.sudo().write(cdr_vals)

            return ""
        else:
            return ""

    @http.route(
        "/mycontactcenter/callCompleted", type="http", auth="public", website=True, sitemap=False
    )
    def intermedia_completed_calls(self, *args, **kw):
        validation = self._check_authentication(**kw)
        if not validation:
            return {'message': 'Invalid API key.', 'status': 403,}

        cdr = (
            request.env["phone.cdr"]
            .sudo()
            .search([("guid", "=", kw.get("GUID"))], limit=1)
        )
        if cdr:
            if cdr.inbound_flag=="inbound":
                customer = kw.get("CallerID")
                caller = kw.get("CallerID")
            else:
                customer = kw.get("CalledID")
                caller = kw.get("AgentId")
            partners = (
                request.env["phone.common"]
                .sudo()
                .get_record_from_phone_number(customer)
            )

            users = (
                request.env["res.users"]
                    .sudo()
                    .search(
                    [
                        ("related_phone", "=", kw.get("AgentId")),
                    ],
                    limit=1,
                )
            )
            if partners:
                return_date = self.convert_into_correct_timezone(kw.get("EndTime"), users)
                cdr_vals = {
                    "call_end_time": return_date,
                    "caller_id": caller,
                    "partner_ids": [(6, 0, partners.ids)],
                    "state": "completed",
                    "call_duration":kw.get("Duration", 0),
                    "call_total_duration":kw.get("TotalDuration", 0)
                }
                cdr.sudo().write(cdr_vals)
                return ""
        return ""

    @http.route(
        "/mycontactcenter/heldCall", type="http", auth="public", website=True, sitemap=False
    )
    def intermedia_held_calls(self, *args, **kw):
        validation = self._check_authentication(**kw)
        if not validation:
            return {'message': 'Invalid API key.', 'status': 403,}

        user = (
            request.env["res.users"]
            .sudo()
            .search(
                [
                    ("related_phone", "=", kw.get("AgentId")),
                ],
                limit=1,
            )
        )
        cdr = (
            request.env["phone.cdr"]
            .sudo()
            .search([("guid", "=", kw.get("GUID"))], limit=1)
        )

        cdr.write({"state": "on_hold"})
        return (
            request.env["phone.common"]
            .sudo()
            .incall_notify_by_login(
                kw.get("CallerID"),
                [user.login],
                calltype="Held Call",
            )
        )

    @http.route(
        "/mycontactcenter/unheldCall", type="http", auth="public", website=True, sitemap=False
    )
    def intermedia_unheld_calls(self, *args, **kw):
        user = (
            request.env["res.users"]
            .sudo()
            .search(
                [
                    ("related_phone", "=", kw.get("AgentId")),
                ],
                limit=1,
            )
        )
        cdr = (
            request.env["phone.cdr"]
            .sudo()
            .search([("guid", "=", kw.get("GUID"))], limit=1)
        )

        cdr.write({"state": "connected"})
        return (
            request.env["phone.common"]
            .sudo()
            .incall_notify_by_login(
                kw.get("CallerID"),
                [user.login],
                calltype="Unheld Call",
            )
        )
