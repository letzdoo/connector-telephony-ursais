import json

from odoo import http
from odoo.http import request, Response
import pytz

from datetime import datetime


class CLOUDCTIVOIP(http.Controller):

    def create_cdr_record(self, user, **kw):
        if kw.get("CallType") == "inbound":
            called_id=user.phone
        else:
            called_id=kw.get("CalledID")
        return_date = self.convert_into_correct_timezone(kw.get("StartTime"), user)
        vals = {
            "guid": kw.get("GUID"),
            "inbound_flag": kw.get("CallType"),
            "caller_id": kw.get("CallerID"),
            "call_start_time": return_date,
            "state": "offering",
            "called_id": called_id,
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

    @http.route(
        "/CloudCTI/incomingCall", type="http", auth="public", website=True, sitemap=False
    )
    def cloudcti_incoming_calls(self, *args, **kw):
        if not kw.get('secret_key') or not kw.get('CallerID') or \
            not kw.get('StartTime') or not kw.get('CallType') or not kw.get('GUID'):
            return Response(json.dumps({'message': 'Missing one of the parameters in Request : \
                secret_key,CallerID, StartTime, CallType, GUID.', 'status': 403}))
        user = (
            request.env["res.users"]
            .sudo()
            .search(
                [
                    ("phone", "=", kw.get("phone")),
                ],
                limit=1,
            )
        )
        if not user:
            return Response(json.dumps({'message': 'User Not found.', 'status': 404}))
        if user:
            cdr = self.create_cdr_record(user, **kw)
            if cdr:
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
                return Response(json.dumps({}))

    @http.route(
        "/CloudCTI/outgoingCall", type="http", auth="public", website=True, sitemap=False
    )
    def cloudcti_outgoing_calls(self, *args, **kw):
        user = (
            request.env["res.users"]
            .sudo()
            .search(
                [
                    ("phone", "=", kw.get("phone")),
                ],
                limit=1,
            )
        )
        if user:
            cdr = self.create_cdr_record(user, **kw)
            if cdr:
                partner = (
                    request.env["phone.common"]
                    .sudo()
                    .get_record_from_phone_number(kw.get("CalledID"))
                )
                cdr_vals = {
                    "caller_id": user.phone,
                    "partner_ids": [(6, 0, partner.ids)],
                    "state": "completed",
                    "user_id": user.id,
                }
                cdr.sudo().write(cdr_vals)
                return Response(json.dumps({}))
        return Response(json.dumps({}))

    @http.route(
        "/CloudCTI/statusChange", type="http", auth="public", website=True, sitemap=False
    )
    def cloudcti_status_change(self, *args, **kw):
        user = (
            request.env["res.users"]
            .sudo()
            .search(
                [
                    ("phone", "=", kw.get("phone")),
                ],
                limit=1,
            )
        )
        if user:
            cdr = self.create_cdr_record(user, **kw)
            if cdr:
                partner = (
                    request.env["phone.common"]
                    .sudo()
                    .get_record_from_phone_number(kw.get("CalledID"))
                )
                cdr_vals = {
                    "caller_id": user.phone,
                    "partner_ids": [(6, 0, partner.ids)],
                    "state": "completed",
                    "user_id": user.id,
                }
                cdr.sudo().write(cdr_vals)
                return Response(json.dumps({}))
        return Response(json.dumps({}))
