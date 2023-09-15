from odoo import fields, models


class ResCompany(models.Model):
    _inherit = "res.company"

    intermedia_user = fields.Char()
    intermedia_password = fields.Char()
    intermedia_server_address = fields.Char("Intermedia API Server Address")
    intermedia_token = fields.Char("Token")
    intermedia_popup_time = fields.Integer(string="Popup Time (Sec)", default=5)

    def get_popup_time(self):
        return self.sudo().intermedia_popup_time

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    popup_time = fields.Integer(
        related='company_id.intermedia_popup_time',
        readonly=False)
