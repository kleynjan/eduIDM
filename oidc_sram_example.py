import base64
import hashlib
import html
import json
import os
import re
from flask import Flask, redirect, request, session
import requests


# helper function
# the code challenge is an encoded string that is used to verify the identity
# of the client the code verifier is a random string that is used to generate
# the code challenge
def get_code_challenge():
    code_verifier = base64.urlsafe_b64encode(os.urandom(40)).decode('utf-8')
    code_verifier = re.sub('[^a-zA-Z0-9]+', '', code_verifier)
    code_challenge = hashlib.sha256(code_verifier.encode('utf-8')).digest()
    code_challenge = base64.urlsafe_b64encode(code_challenge).decode('utf-8')
    code_challenge = code_challenge.replace('=', '')
    return code_verifier, code_challenge


# request the initial authorization code from the SRAM server
def get_auth_url():
    return requests.get(
        url=app.config['authorization_endpoint'],
        params={
            "response_type": "code",
            "client_id": app.config['CLIENT_ID'],
            "scope": "openid profile email",
            "redirect_uri": app.config['REDIRECT_URI'],
            "code_challenge": code_challenge,
            "code_challenge_method": "S256",
        },
        allow_redirects=False
    ).url


# request the access token from the SRAM server using the code from the previous step
def get_access_token(code, code_verifier):
    token_params = {
        'grant_type': 'authorization_code',
        'code': code,
        'client_id': app.config['CLIENT_ID'],
        'client_secret': app.config['CLIENT_SECRET'],
        'redirect_uri': app.config['REDIRECT_URI'],
        'code_verifier': code_verifier,
    }
    result = requests.post(app.config['token_endpoint'], data=token_params)
    if (result.status_code != 200):
        return None
    return result.json()


# determine if the user is logged in
def is_logged_in():
    return 'access_token' in session


# get the userinfo from the SRAM server using the access token from the previously retrieved access token
def get_userinfo(access_token):
    if (is_logged_in() is False):
        return None
    result = requests.post(url=app.config['userinfo_endpoint'], data=access_token)
    if (result.status_code != 200):
        return None
    return result.json()


# get config from .well-known endpoint
def get_config(url):
    result = requests.get(url)
    if result.status_code == 200:
        return json.loads(result.content)
    return {}


app = Flask(__name__)
app.secret_key = os.urandom(24)

# read the configuration from the config.json file
with open('config.json') as config_file:
    config = json.load(config_file)
    app.config.update(config)
    config_url = config['DOTWELLKNOWN']
    app.config.update(get_config(config_url))


# call the helper function to get the code verifier and code challenge
code_verifier, code_challenge = get_code_challenge()


# the login route redirects the user to authorization URL of the SRAM server
@app.route('/login')
def login():
    return redirect(get_auth_url())


# the authorization callback route is called by the SRAM server after the user
# has logged in
@app.route('/oidc_callback')
def oidc_callback():
    code = request.args['code']
    access_token = get_access_token(code, code_verifier)
    if access_token is None:
        return "Error while getting access token"
    session['access_token'] = access_token
    return redirect('/')


# the logout route clears the session and redirects the user to the home page
@app.route('/logout')
def logout():
    session.pop('access_token', None)
    return redirect('/')


# the home route displays the user information if the user is logged in
# else it shows that the user is not logged in
@app.route('/')
def home():
    if is_logged_in():
        access_token = session['access_token']
        userinfo = get_userinfo(access_token)
        return f"""
 <p>Welcome, {html.escape(userinfo['name'])}!</p>
 <p>Your email is {html.escape(userinfo['email'])}</p>
 <p>You may now access the private page <a href='/private'>here</a></p>
 <p><a href="/logout">Logout</a></p>
 """
    return "<p>Welcome!<br/><a href='/login'>Login here</a></p>"

# the private page is only displayed if the user is logged in
# else it shows that the user is not logged in
@app.route('/private')
def private():
    if not is_logged_in():
        return "<p>You are not logged in.<br/><a href='/login'>Login here</a></p>"
    return "Very confidential and private page!"


# run the app and make sure we are in debug mode
if __name__ == '__main__':
    # app.run(host='127.0.0.1', port=8080, debug=True, ssl_context='adhoc')
    app.run(host='127.0.0.1', port=8080, debug=True)
