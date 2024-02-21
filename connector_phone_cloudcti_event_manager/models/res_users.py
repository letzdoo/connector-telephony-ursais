import requests
from datetime import datetime
from dateutil.relativedelta import relativedelta
from requests.auth import HTTPBasicAuth

from odoo import models, fields, _
from odoo.exceptions import UserError


class ResUsers(models.Model):
    _inherit = "res.users"

    cloudcti_token = fields.Char("Token")
    token_expiration_time = fields.Datetime("Expiration Time")

    def generate_cloudcti_access_token(self):
        for user in self:
            credentials = user.partner_id._get_cloudcti_credentials(user)
            auth_token_url = credentials['sign_address'] + "/token"
            try:
                response = requests.get(
                    url=auth_token_url,
                    auth=HTTPBasicAuth(
                        credentials.get("cloudcti_username"),
                        credentials.get("cloudcti_password")
                    ),
                )
                response.raise_for_status()
                response_data = response.json()
                access_token = response_data["SecurityToken"]
                expiration_time = response_data["SecurityTokenExpirationTime"]
            except (
                requests.exceptions.HTTPError,
                requests.exceptions.RequestException,
                requests.exceptions.ConnectionError,
            ) as err:
                raise UserError(
                    _("Error! \n Could not retrive token from CloudCTI. %s") % (err)
                ) from err
            user.sudo().write(
                {
                    "cloudcti_token": access_token,
                    "token_expiration_time": expiration_time
                }
            )
