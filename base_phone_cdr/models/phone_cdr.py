from odoo import api, fields, models


class PhoneCDR(models.Model):
    _name = "phone.cdr"
    _description = "Phone CDR"

    @api.depends("call_start_time", "call_connect_time", "inbound_flag")
    def _compute_ring_time(self):
        for rec in self:
            if rec.inbound_flag and rec.call_connect_time and rec.call_start_time:
                duration = rec.call_connect_time - rec.call_start_time
                duration_in_s = duration.total_seconds()
                rec.ring_time = divmod(duration_in_s, 3600)[0]

    guid = fields.Char("Call GUID")
    inbound_flag = fields.Selection(
        [("outbound", "Outbound"), ("inbound", "Inbound")], string="Call Inbound flag"
    )
    call_start_time = fields.Datetime("Call start time")
    call_end_time = fields.Datetime("Call end time")
    call_connect_time = fields.Datetime("Call connect time")
    call_duration = fields.Char("Duration")
    call_total_duration = fields.Char("Total Duration")
    ring_time = fields.Float(compute="_compute_ring_time", string="Compute ring time")
    talk_time = fields.Datetime("Talk Time")
    caller_id = fields.Char("Caller ID")
    called_id = fields.Char("Called ID")
    called_id_name = fields.Char("Called ID Name")
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
    user_id = fields.Many2one(
        "res.users", string="Odoo User"
    )
    partner_ids = fields.Many2many("res.partner",
                                   "partner_cdr_rel",
                                   "cdr_id",
                                   "partner_id",
                                   string="Partner")