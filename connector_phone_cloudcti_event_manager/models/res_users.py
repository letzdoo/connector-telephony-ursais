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
        credentials = self.partner_id._get_cloudcti_credentials()
        auth_token_url = credentials['sign_address'] + "/token" 
        try:
            headers = {"content-type": "application/json"}
            response = requests.get(
                url=auth_token_url,
                auth=HTTPBasicAuth(credentials.get("cloudcti_username"), credentials.get("cloudcti_password")),
            )
            response.raise_for_status()
            response_data = response.json()
            access_token = response_data["SecurityToken"]
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
