from odoo import http
from odoo.http import request


class PCSVOIP(http.Controller):

    def create_cdr_record(self, **kw):
        if kw.get("Inbound") == "1":
            inbound_flag = "inbound"
        else:
            inbound_flag = "outbound"
        vals = {
            "guid": kw.get("GUID"),
            "inbound_flag": inbound_flag,
            "call_start_time": kw.get("StartTime"),
            "state": "offering",
            "called_id": kw.get("CalledID"),
        }
        return request.env["phone.cdr"].sudo().create(vals)

    @http.route(
        "/palitto/incomingCall", type="http", auth="public", website=True, sitemap=False
    )
    def pcs_incoming_calls(self, *args, **kw):
        user = (
            request.env["res.users"]
            .sudo()
            .search(
                [
                    ("related_phone", "=", kw.get("CalledID")),
                ],
                limit=1,
            )
        )
        cdr = self.create_cdr_record(**kw)
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
            return False

    @http.route(
        "/palitto/outgoingCall", type="http", auth="public", website=True, sitemap=False
    )
    def pcs_outgoing_calls(self, *args, **kw):

        user = (
            request.env["res.users"]
            .sudo()
            .search(
                [
                    ("related_phone", "=", kw.get("CallerID")),
                ],
                limit=1,
            )
        )

        cdr = self.create_cdr_record(**kw)

        if cdr:
            partner = (
                request.env["phone.common"]
                .sudo()
                .get_record_from_phone_number(kw.get("CalledID"))
            )
            cdr_vals = {
                "caller_id": kw.get("CallerID"),
                "partner_ids": [(6, 0, partner.ids)],
                "state": "completed",
                "user_id": user.id,
            }
            cdr.sudo().write(cdr_vals)
            return True
        else:
            return False

    @http.route(
        "/palitto/missedCall", type="http", auth="public", website=True, sitemap=False
    )
    def pcs_missedCall_calls(self, *args, **kw):
        user = (
            request.env["res.users"]
            .sudo()
            .search(
                [
                    ("related_phone", "=", kw.get("CalledID")),
                ],
                limit=1,
            )
        )
        cdr = (
            request.env["phone.cdr"]
            .sudo()
            .search([("guid", "=", kw.get("GUID"))], limit=1)
        )
        # ToDo Calculate End time
        if cdr:
            partner = (
                request.env["phone.common"]
                .sudo()
                .get_record_from_phone_number(kw.get("CallerID"))
            )
            cdr_vals = {
                "call_end_time": kw.get("EndTime"),
                "caller_id": kw.get("CallerID"),
                "partner_ids": [(6, 0, partner.ids)],
                "state": "missed",
                "user_id": user.id,
            }
            cdr.sudo().write(cdr_vals)

            return True
        else:
            False

    @http.route(
        "/palitto/callCompleted", type="http", auth="public", website=True, sitemap=False
    )
    def pcs_completed_calls(self, *args, **kw):
        user = (
            request.env["res.users"]
            .sudo()
            .search(
                [
                    ("related_phone", "=", kw.get("CallerID")),
                ],
                limit=1,
            )
        )
        cdr = (
            request.env["phone.cdr"]
            .sudo()
            .search([("guid", "=", kw.get("GUID"))], limit=1)
        )
        partners = (
            request.env["phone.common"]
            .sudo()
            .get_record_from_phone_number(kw.get("CalledID"))
        )
        if partners:
            cdr_vals = {
                "call_end_time": kw.get("EndTime"),
                "caller_id": kw.get("CallerID"),
                "partner_ids": [(6, 0, partners.ids)],
                "state": "completed",
                "call_duration":kw.get("Duration", 0),
                "call_total_duration":kw.get("TotalDuration", 0)
            }
            cdr.sudo().write(cdr_vals)
            return True
        return None

    @http.route(
        "/palitto/heldCall", type="http", auth="public", website=True, sitemap=False
    )
    def pcs_held_calls(self, *args, **kw):
        user = (
            request.env["res.users"]
            .sudo()
            .search(
                [
                    ("related_phone", "=", kw.get("CalledID")),
                ],
                limit=1,
            )
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
            .incall_notify_by_login(
                kw.get("CallerID"),
                [user.login],
                calltype="Held Call",
            )
        )

    @http.route(
        "/palitto/unheldCall", type="http", auth="public", website=True, sitemap=False
    )
    def pcs_unheld_calls(self, *args, **kw):
        user = (
            request.env["res.users"]
            .sudo()
            .search(
                [
                    ("related_phone", "=", kw.get("CalledID")),
                ],
                limit=1,
            )
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
            .incall_notify_by_login(
                kw.get("CallerID"),
                [user.login],
                calltype="Unheld Call",
            )
        )
