import os 
import requests
from requests_oauthlib import OAuth2Session
from authlib.jose import jwt

os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"
os.environ["OAUTHLIB_RELAX_TOKEN_SCOPE"] = "1"

# Credentials you get from registering a new application
client_id = 
client_secret = "
redirect_uri = 'https://validate.buildingsmart.org/'

# OAuth endpoints given in the bSDD API documentation
authorization_base_url = 'https://buildingsmartservices.b2clogin.com/buildingsmartservices.onmicrosoft.com/b2c_1a_signupsignin_c/oauth2/v2.0/authorize'
token_url = 'https://buildingSMARTservices.b2clogin.com/buildingSMARTservices.onmicrosoft.com/b2c_1a_signupsignin_c/oauth2/v2.0/token'
bs = OAuth2Session(client_id, redirect_uri=redirect_uri, scope=["openid profile","https://buildingSMARTservices.onmicrosoft.com/api/read"])

# Redirect user to bs for authorization
authorization_url, state = bs.authorization_url(authorization_base_url)
print('Please go here and authorize,', authorization_url)

# Get the authorization verifier code from the callback url
redirect_response = input('Paste the full redirect URL here:')

# Fetch the access token
t = bs.fetch_token(token_url, client_secret=client_secret, authorization_response=redirect_response, response_type="token")

# Get openid info
BS_DISCOVERY_URL = (
    "https://buildingSMARTservices.b2clogin.com/buildingSMARTservices.onmicrosoft.com/b2c_1a_signupsignin_c/v2.0/.well-known/openid-configuration"
)
discovery_response = requests.get(BS_DISCOVERY_URL).json()

# Get claims thanks to openid
key = requests.get(discovery_response['jwks_uri']).content.decode("utf-8")
id_token = t['id_token']
decoded = jwt.decode(id_token, key=key)





