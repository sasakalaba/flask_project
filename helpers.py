import json
from requests import PreparedRequest
from requests.structures import CaseInsensitiveDict
from requests.compat import OrderedDict
from requests.cookies import RequestsCookieJar
from stormpath.auth import Sauthc1Signer
from stormpath.client import Client
from stormpath.resources import FactorList, Factor
from pydispatch import dispatcher
from pprint import pprint


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
    def assert_values(value1, value2, value_info):
        if value1 != value2:
            error_msg = '%s != %s' % (str(value1), str(value2))
            raise AssertionError({'error': error_msg, 'value': value_info})

    def assert_headers(headers, expected_headers):
        x_date = headers.pop('X-Stormpath-Date')
        x_date_expected = expected_headers.pop('X-Stormpath-Date')
        auth = headers.pop('Authorization')
        auth_expected = expected_headers.pop('Authorization')
        headers.pop('User-Agent')
        expected_headers.pop('User-Agent')

        assert_values(len(x_date), len(x_date_expected), 'x_date')
        assert_values(len(auth), len(auth_expected), 'auth')
        assert_values(headers, expected_headers, 'headers')

    # Compare requests
    attrs = ['url', 'method', 'body']

    for attr in attrs:
        value = getattr(req, attr)
        expected_value = getattr(expected_req, attr)

        if attr == 'body':
            assert_values(json.loads(value), json.loads(expected_value), attr)
        else:
            assert_values(value, expected_value, attr)

    assert_headers(req.headers, expected_req.headers)

    # Compare responses
    attrs = ['url', 'status_code']

    for attr in attrs:
        value = getattr(resp, attr)
        expected_value = expected_resp.get(attr)

        assert_values(value, expected_value, attr)

    print '\n'
    pprint(json.loads(resp.content))
    print '\n'

    return None


def delete_resource(client, acc_url, resource):
    client.accounts.get(acc_url).factors.items[0]
    res_list = getattr(client.accounts.get(acc_url), resource + 's').items
    if len(res_list) == 1:
        res_list[0].delete()
    else:
        raise Exception('Resource cannot be deleted.')

    return None


def main():
    # Additional imports
    import os

    # Reset flag
    os.environ['MYFLAG'] = 'notbar'

    # Set variables
    resource_name = 'factor'
    acc_url = 'https://api.stormpath.com/v1/accounts/6FZ1uG8uXob6TrxJJQB9j2'
    method = 'POST'
    url = 'https://api.stormpath.com/v1/accounts/6FZ1uG8uXob6TrxJJQB9j2/factors?challenge=true'
    body = {
        "phone": {"number": "+385 995734532"},
        "challenge": {"message": "${code}"},
        "type": "SMS"}
    status_code = 201

    expected_response = {
        'url': url,
        'status_code': status_code}

    # Environ variables
    os.environ['expected_resp'] = json.dumps(expected_response)
    os.environ['exp_req_method'] = method
    os.environ['exp_req_url'] = url
    os.environ['exp_req_body'] = json.dumps(body)

    # Main
    resources = get_resources()
    client = resources['client']

    # Set flag
    os.environ['MYFLAG'] = 'foobar'

    try:
        created = eval(resource_name.title())(
            client,
            properties=client.data_store.create_resource(
                url, body, params=None))
    except Exception as error:
        os.environ['MYFLAG'] = 'notbar'
        delete_resource(client, acc_url, resource_name)
        return error

    # Reset flag
    os.environ['MYFLAG'] = 'notbar'

    delete_resource(client, acc_url, resource_name)
    print '\nSUCCESS\n'
    return None
