from odoo import fields, models


class ResCompany(models.Model):
    _inherit = "res.company"

    cloudcti_url = fields.Char("CloudCTI URL", default="https://api.cloudcti.nl/api/v2")
    cloudcti_popup_time = fields.Integer(string="Popup Time (Sec)", default=5)

    def get_popup_time(self):
        return self.sudo().cloudcti_popup_time

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    popup_time = fields.Integer(
        related='company_id.cloudcti_popup_time',
        readonly=False)
