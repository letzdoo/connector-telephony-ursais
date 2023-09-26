from odoo import fields, models


class ResUsers(models.Model):
    _inherit = "res.users"

    intermedia_agentid = fields.Char()
    intermedia_agent_phone = fields.Char()
