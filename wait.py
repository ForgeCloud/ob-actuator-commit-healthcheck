#!/usr/bin/env python

import os
from distutils.util import strtobool
from time import sleep

import requests
from requests import RequestException

requests_session = requests.Session()


def is_up(auth):
    url = os.getenv("URL")
    try:
        resp = requests_session.get(f'{url}/actuator/health', auth=auth, timeout=5)
        if resp.status_code != 200:
            print(f'health http_status={resp.status_code}')
            return False
        health = resp.json()
        health_status = health['status']
        print(f'status={health_status}')
        return health_status == 'UP'
    except RequestException:
        return False


def is_on_commit(auth, commit):
    url = os.getenv("URL")
    try:
        resp = requests_session.get(f'{url}/actuator/info', auth=auth, timeout=5)
        if resp.status_code != 200:
            print(f'info http_status={resp.status_code}')
            return False
        info = resp.json()
        server_commit = info['git']['commit']['id']
        print(f'expected_commit={commit} server_commit={server_commit}')
        return server_commit in commit
    except RequestException:
        return False


def retry_until_healthy(auth, timeout, retries, commit_id):
    for i in range(0, retries):
        on_commit = is_on_commit(auth, commit_id)
        up = is_up(auth)
        if on_commit and up:
            print('Service is up')
            exit(0)
        print(f'Waiting timeout={timeout}')
        sleep(timeout)


if __name__ == '__main__':
    if not os.getenv("URL") or not os.getenv("COMMIT"):
        print('Set environment variables URL and COMMIT')
        exit(1)

    if not strtobool(os.getenv("SSL_VERIFY", "True")):
        requests_session.verify = False
        import urllib3

        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

    timeout = int(os.getenv('TIMEOUT', 1))
    retries = int(os.getenv('RETRIES', 60))
    commit_id = os.getenv('COMMIT')
    auth = (os.getenv('USERNAME'), os.getenv('PASSWORD')) if os.getenv('USERNAME') and os.getenv('PASSWORD') else None
    retry_until_healthy(auth, timeout, retries, commit_id)

    print(f'Timed out after {timeout * retries} seconds')
    exit(1)
