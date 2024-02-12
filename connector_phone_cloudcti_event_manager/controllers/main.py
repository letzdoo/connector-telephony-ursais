import json

from odoo import http
from odoo.http import request, Response
import pytz

from datetime import datetime

'''
    #CDR Fields for local reference
    call_start_time = fields.Datetime("Call start time")
    call_end_time = fields.Datetime("Call end time")
    call_duration = fields.Char("Duration")
    caller_id = fields.Char("Caller ID")
    called_id = fields.Char("Called ID")
    state = fields.Selection(
        [
            ("offering", "Offering"),
            ("connected", "Connected"),
            ("missed", "Missed"),
            ("completed", "Completed"),
            ("on_hold", "On Hold"),
        ],
        string="Status",
        default="offering",
    )
'''

class CloudCTIVOIP(http.Controller):

    def map_state(self, instate, currentstate = False):
        if instate == 'ringing':
            outstate = 'offering'
        elif instate == 'answered':
            outstate = 'connected'
        elif instate == 'ended':
            if currentstate == 'offering':
                outstate = 'missed'
            elif currentstate == 'connected':
                outstate = 'completed'
        else:
            outstate = 'on_hold'

    def create_cdr_record(self, user, payload):
        return_date = self.convert_into_correct_timezone(payload.get("starttime"), user)
        vals = {
            "guid": payload.get("callid"),
            "inbound_flag": payload.get("direction"),
            "called_id": payload.get("calledid"),
            "called_id_name": user.name,
            "caller_id": payload.get("callerid"),
            "call_start_time": return_date,
            "state": map_state(payload.get("state")),
            "user_id": user.id,
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
        "/CloudCTI/statusChange", type="http", auth="public", website=True, sitemap=False
    )
    def cloudcti_status_change(self, *args, **kw):
        # check for data
        if len(**kw):
            guid = kw.get("CallId")
            callednumber = kw.get("CalledNumber")
            callernumber = kw.get("CallerNumber")
            direction = kw.get("Direction")
            state = kw.get("State")
            starttime = kw.get("StartTime") or False
            endtime = kw.get("EndTime") or False
            duration = kw.get("CallDuration") or 0.0
        else:
            return Response(json.dumps({}))

        if direction == "inbound":
           phone = callednumber 
           other = callernumber
           if state == "ringing":
               create = True
               update = False
           else:
               create = False
               update = True
        elif direction == "outbound":
           phone = callernumber 
           other = callednumber
           if state == "ringing":
               create = True
               update = False
           else:
               create = False
               update = True
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
        else:
            partner = (
                request.env["phone.common"]
                .sudo()
                .get_record_from_phone_number(other)
            )
            if create:
                payload = { "callid": guid, "callerid":other, "calledid":phone, "direction":direction, "state":state,"starttime":starttime, "partner_ids":[(6,0, partner.ids)]}
                cdr = self.create_cdr_record(user, payload)
                if direction == "inbound" and cdr:
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
            else:
                cdr = (
                    request.env["phone.cdr"]
                    .sudo()
                    .search([("guid", "=", guid)], limit=1)
                )
                return_date = self.convert_into_correct_timezone(endtime, user)
                payload = { "state":map_state(state,cdr.state),"call_end_time":return_date, "call_duration": duration}
                cdr.sudo().write(cdr_vals)
        return Response(json.dumps({}))
