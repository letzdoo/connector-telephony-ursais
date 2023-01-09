from odoo import fields, models


class ResCompany(models.Model):
    _inherit = "res.company"

    server_address = fields.Char("PCS API Server Address")
    popup_time = fields.Integer(string="Popup Time (Sec)", default=5)

    def get_popup_time(self):
        return self.sudo().popup_time


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    popup_time = fields.Integer(
        related='company_id.popup_time',
        readonly=False)
