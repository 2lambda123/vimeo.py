"""
Licensed to the Apache Software Foundation (ASF) under one
or more contributor license agreements.  See the NOTICE file
distributed with this work for additional information
regarding copyright ownership.  The ASF licenses this file
to you under the Apache License, Version 2.0 (the
"License"); you may not use this file except in compliance
with the License.  You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing,
software distributed under the License is distributed on an
"AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
KIND, either express or implied.  See the License for the
specific language governing permissions and limitations
under the license.
"""

import urllib
import base64
import json
from copy import copy

from tornado.httpclient import HTTPClient


def get_auth_url(api_root, cid, scopes, redirect):
    """
    Generates the authorization url necessary to create an access token for a user.
    The url generated by this function points to a page prompting the user to
    allow or deny access on the part of this app to their account, dictated by
    the given scopes.

    In the context of a web server, the programmer should direct the user to the URL
    returned by this function. Doing so amounts to starting the OAuth2 authorization
    flow.

    Note: The following URLs must be identical:
        This function's redirect parameter
        The redirect parameter passed to get_access_token
        One of the redirect URIs listed on the app setup page

    Args:
    api_root    - The root url of the API being used (in VimeoClient, accessible via
                  config['apiroot']
    cid         - The client ID for the current app
    scopes      - A list of permission scopes that the user will be prompted to allow
    redirect    - The redirect URI for the app (see above note)

    returns the full URL for auth code generation
    """
    choices = ['interact', 'private', 'public', 'create',
               'edit', 'delete', 'upload']
    auth_url = "%s/oauth/authorize?response_type=code&client_id=%s&scope=" % \
            (api_root, cid)
    if not scopes:
        scopes = copy(choices)
    for scope in scopes:
        if scope not in choices:
            raise ValueError("Scope must be one of %s (found scope '%s')" % (choices, scope))
        auth_url += "%s+" % scope
    auth_url += "&redirect_uri=%s" % (redirect)
    return auth_url

def get_access_token(auth_code, cid, secret, redirect, api_root='https://api.vimeo.com'):
    """
    Generates a new access token given the authorization code generated by the page
    at get_auth_url().

    In the context of a web server, the programmer should retrieve the auth_code
    generated by the page at get_auth_url() and use it as the input to this function.
    The programmer should then use the string returned from this function to
    authenticate calls to the API library on behalf of the corresponding user.

    Note: The following URLs must be identical:
        This function's redirect parameter
        The redirect parameter passed to get_access_token
        One of the redirect URIs listed on the app setup page

    Args:
    auth_code   - The authorization code given in the 'code' query parameter of the
                  page URI after redirecting from the result of get_auth_url
    cid         - The client ID for the current app
    secret      - The client secret for the current app
    redirect    - The redirect URI for the app (see note)
    api_root    - The root url of the API being used (in VimeoClient, accessible via
                  config['apiroot']
    """
    encoded = base64.b64encode("%s:%s" % (cid, secret))

    payload = {"grant_type": "authorization_code",
            "code": auth_code,
            "redirect_uri": redirect}
    headers = {"Accept": "application/vnd.vimeo.*+json; version=3.2",
            "Authorization": "Basic %s" % encoded}

    response = HTTPClient().fetch("%s/oauth/access_token" % api_root,
                          method="POST",
                          headers=headers,
                          body=urllib.urlencode(payload),
                          validate_cert=True)
    if response.error:
        raise ValueError(response.error)
    else:
        return json.loads(response.body)['access_token']

def get_client_credentials(client_id, client_secret, scopes=None, api_root='https://api.vimeo.com'):
    """
    Generates a bearer token for the registered application.

    This token will exist without a user context, but will allow for access to data in the API.

    Args:
    client_id     - The client ID for the current app
    client_secret - The client secret for the current app
    scopes        - A list of permission scopes that the user will be prompted to allow
    api_root      - The root url of the API being used (in VimeoClient, accessible via
                  config['apiroot'])
    """
    basic_auth = base64.b64encode("%s:%s" % (client_id, client_secret))
    payload = {"grant_type": "client_credentials"}
    headers = {"Accept": "application/vnd.vimeo.*+json; version=3.2",
            "Authorization": "Basic %s" % basic_auth}

    if scopes:
        payload['scope'] = scopes

    response = HTTPClient().fetch("%s/oauth/authorize/client" % api_root,
                          method="POST",
                          headers=headers,
                          body=urllib.urlencode(payload))

    if response.error:
        raise ValueError(response.error)

    return json.loads(response.body)['access_token']
