from odoo import http
from odoo.http import request


class PCSVOIP(http.Controller):
    def create_cdr_record(self, **kw):
        if kw.get("Inbound") == 1:
            inbound_flag = "inbound"
        else:
            inbound_flag = "outbound"
        vals = {
            "guid": kw.get("GUID"),
            "inbound_flag": inbound_flag,
            "call_start_time": kw.get("StartTime"),
            "caller_id": kw.get("CallerID"),
            "state": "offering",
        }
        return request.env["phone.cdr"].sudo().create(vals)

    @http.route(
        "/palitto/incomingCall", type="http", auth="public", website=True, sitemap=False
    )
    def pcs_incoming_calls(self, *args, **kw):
        user = (
            request.env["res.users"]
            .sudo()
            .search([("related_phone", "=", kw.get("Ext"))], limit=1)
        )
        self.create_cdr_record(**kw)
        return (
            request.env["phone.common"]
            .sudo()
            .incall_notify_by_login(kw.get("CallerID"), [user.login])
        )

    @http.route(
        "/palitto/Call", type="http", auth="public", website=True, sitemap=False
    )
    def pcs_outgoing_calls(self, *args, **kw):
        user = (
            request.env["res.users"]
            .sudo()
            .search([("phone", "=", kw.get("CallerID"))], limit=1)
        )
        self.create_cdr_record(**kw)
        return (
            request.env["phone.common"]
            .sudo()
            .incall_notify_by_login(kw.get("CallerID"), [user.login])
        )

    @http.route(
        "/palitto/missedCall", type="http", auth="public", website=True, sitemap=False
    )
    def pcs_missedCall_calls(self, *args, **kw):
        user = (
            request.env["res.users"]
            .sudo()
            .search([("phone", "=", kw.get("CallerID"))], limit=1)
        )
        cdr = (
            request.env["phone.cdr"]
            .sudo()
            .search([("guid", "=", kw.get("GUID"))], limit=1)
        )
        # ToDo Calculate End time
        cdr.write({"state": "missed"})
        return (
            request.env["phone.common"]
            .sudo()
            .incall_notify_by_login(kw.get("CallerID"), [user.login])
        )

    @http.route(
        "/palitto/Completed", type="http", auth="public", website=True, sitemap=False
    )
    def pcs_completed_calls(self, *args, **kw):
        user = (
            request.env["res.users"]
            .sudo()
            .search([("phone", "=", kw.get("CallerID"))], limit=1)
        )
        cdr = (
            request.env["phone.cdr"]
            .sudo()
            .search([("guid", "=", kw.get("GUID"))], limit=1)
        )
        # ToDo - Calculate ring time & talk time
        cdr.write({"state": "completed"})
        return (
            request.env["phone.common"]
            .sudo()
            .incall_notify_by_login(kw.get("CallerID"), [user.login])
        )

    @http.route(
        "/palitto/heldCall", type="http", auth="public", website=True, sitemap=False
    )
    def pcs_held_calls(self, *args, **kw):
        user = (
            request.env["res.users"]
            .sudo()
            .search([("phone", "=", kw.get("CallerID"))], limit=1)
        )
        cdr = (
            request.env["phone.cdr"]
            .sudo()
            .search([("guid", "=", kw.get("GUID"))], limit=1)
        )
        # ToDo - Calculate hold time
        cdr.write({"state": "on_hold"})
        return (
            request.env["phone.common"]
            .sudo()
            .incall_notify_by_login(kw.get("CallerID"), [user.login])
        )

    @http.route(
        "/palitto/unheldCall", type="http", auth="public", website=True, sitemap=False
    )
    def pcs_unheld_calls(self, *args, **kw):
        user = (
            request.env["res.users"]
            .sudo()
            .search([("phone", "=", kw.get("CallerID"))], limit=1)
        )
        cdr = (
            request.env["phone.cdr"]
            .sudo()
            .search([("guid", "=", kw.get("GUID"))], limit=1)
        )
        # ToDo - Calculate unheld time
        cdr.write({"state": "connected"})
        return (
            request.env["phone.common"]
            .sudo()
            .incall_notify_by_login(kw.get("CallerID"), [user.login])
        )
