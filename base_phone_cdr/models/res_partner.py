from ast import literal_eval

from odoo import api, fields, models


class ResPartner(models.Model):
    _inherit = "res.partner"

    total_cdr_count = fields.Integer(
        compute="_compute_total_cdr_count", string="Total CDR"
    )

    def _compute_total_cdr_count(self):
        for partner in self:
            query = """select count(cdr_id) from partner_cdr_rel \
                where partner_id=%s""" % partner.id
            self._cr.execute(query)
            records = self._cr.fetchall()
            partner.total_cdr_count = records[0][0] if records else 0

    @api.multi
    def action_view_partner_cdr_records(self):
        self.ensure_one()
        action = self.env.ref("base_phone_cdr.phone_cdr_view_action").read()[0]
        action["domain"] = literal_eval(action["domain"])
        query = """select cdr_id from partner_cdr_rel \
            where partner_id=%s""" % self.id
        self._cr.execute(query)
        cdr_records = [row[0] for row in self._cr.fetchall()]
        action["domain"].append(("id", "in", cdr_records))
        return action
