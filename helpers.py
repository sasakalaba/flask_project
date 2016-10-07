import json
from requests import PreparedRequest
from requests.structures import CaseInsensitiveDict
from requests.compat import OrderedDict
from requests.cookies import RequestsCookieJar
from stormpath.auth import Sauthc1Signer
from stormpath.client import Client
from stormpath.resources import FactorList
from pydispatch import dispatcher


def generate_request(method, url, body):
    """
    Generate our own custom request, so we can calculate digest auth.
    """
    method = method.upper()
    url = url
    files = []
    body = body
    json_string = None
    headers = CaseInsensitiveDict({
        'Accept': 'application/json',
        'Accept-Encoding': 'gzip, deflate',
        'Connection': 'keep-alive',
        'Content-Length': str(len(json.dumps(body))),
        'Content-Type': 'application/json',
        'User-Agent': 'stormpath-flask/0.4.4 flask/0.10.1 stormpath-sdk-python/2.4.5 python/2.7.6 Linux/LinuxMint (Linux-3.13.0-37-generic-x86_64-with-LinuxMint-17.1-rebecca)'
    })
    params = OrderedDict()
    auth = Sauthc1Signer(
        id='34T89RR6UW2JWTTUCB0CF8D87',
        secret='m2dPlw8ql20JdyPKA5uUB3Ppgs4nNSp45IJsqRRdp0g')
    cookies = RequestsCookieJar()
    hooks = {'response': []}

    pr = PreparedRequest()
    pr.prepare(
        method=method.upper(),
        url=url,
        files=files,
        data=json.dumps(body),
        json=json_string,
        headers=headers,
        params=params,
        auth=auth,
        cookies=cookies,
        hooks=hooks,
    )

    return pr


def get_resources():
    """
    Load all objects needed for developing new Stormpath resources.
    """

    credentials = {
        'STORMPATH_API_KEY_ID': '34T89RR6UW2JWTTUCB0CF8D87',
        'STORMPATH_API_KEY_SECRET': "m2dPlw8ql20JdyPKA5uUB3Ppgs4nNSp45IJsqRRdp0g",
    }
    AUTH_SCHEME = 'SAuthc1'

    client = Client(
        id=credentials['STORMPATH_API_KEY_ID'],
        secret=credentials['STORMPATH_API_KEY_SECRET'],
        base_url='https://api.stormpath.com/v1',
        scheme=AUTH_SCHEME)

    client.tenant.refresh()

    resources = {
        'client': client
    }

    return resources


def custom_create(cls, client, data, href, params=None):
    """
    Resource create. Currently bypassing base.py create() method.
    """
    SIGNAL_RESOURCE_CREATED = 'resource-created'

    instance = cls(client=client, href=href)
    created = instance.resource_class(
        instance._client,
        properties=instance._store.create_resource(
            instance._get_create_path(), data, params=params))
    dispatcher.send(
        signal=SIGNAL_RESOURCE_CREATED,
        sender=instance.resource_class,
        data=data,
        params=params)

    return created


def assert_request(req, resp, expected_req, expected_resp):
    """
    Make sure that the request and response match the one we are trying to get.
    """
    def assert_headers(headers, expected_headers):
        x_date = headers.pop('expected_value')
        x_date_expected = expected_headers.pop('expected_value')
        auth = headers.pop('Authorization')
        auth_expected = expected_headers.pop('Authorization')

        assert len(x_date) == len(x_date_expected)
        assert len(auth) == len(auth_expected)
        assert headers == expected_headers

    # Compare requests
    attrs = ['url', 'method', 'body']

    for attr in attrs:
        value = getattr(req, attr)
        expected_value = getattr(expected_req, attr)

        if attr == 'body':
            assert json.loads(value) == json.loads(expected_value)
        elif attr == 'headers':
            assert_headers(value, expected_value)
        else:
            assert value == expected_value

    # Compare responses
    attrs = ['url', 'status_code', 'content']

    for attr in attrs:
        value = getattr(resp, attr)
        expected_value = expected_resp.get(attr)

        if attr == 'content':
            assert json.loads(value) == expected_value
        else:
            assert value == expected_value
