import requests
from datetime import datetime
from dateutil.relativedelta import relativedelta

from odoo import _, api, fields, models
from odoo.exceptions import UserError


class ResUsers(models.Model):
    _inherit = "res.users"

    cloudcti_token = fields.Char("Token")
    token_expiration_time = fields.Datetime("Expiration Time")

    def generate_cloudcti_access_token(self):
        import pdb;pdb.set_trace()
        credentials = self.partner_id._get_cloudcti_credentials()
        auth_token_url = credentials['sign_address'] + "/token" 
        token_data = {
            "grant_type": "account_credentials",
            "cloudcti_username": self.phone,
            "cloudcti_password": self.phone_password,
        }
        try:
            response = requests.post(
                auth_token_url,
                auth=(self.phone, self.phone_password),
                data=token_data,
                timeout=30,
            )
            response.raise_for_status()
            response_data = response.json()
            access_token = response_data["access_token"]
        except (
            requests.exceptions.HTTPError,
            requests.exceptions.RequestException,
            requests.exceptions.ConnectionError,
        ) as err:
            raise UserError(
                _("Error! \n Could not retrive token from CloudCTI. %s") % (err)
            ) from err
        self.cloudcti_token = access_token
        self.token_expiration_time = datetime.now() + relativedelta(days=1)
