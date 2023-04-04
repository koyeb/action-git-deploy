#!/usr/bin/env python

import argparse
import json
import subprocess


def koyeb_get_last_deployment_id(*, app_name, service_name):
    """Wrapper around koyeb CLI to get the last deployment ID of a service.
    Assumes that the koyeb CLI is installed and configured."""
    proc = subprocess.run([
        'koyeb', 'service', 'get',
        f'{app_name}/{service_name}',
        '-o', 'json'
    ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    if proc.returncode != 0:
        stderr = proc.stderr.decode()
        raise RuntimeError(
            f'Error while getting the last deployment of {app_name}/{service_name}\n{"v" * 100}\n{stderr.strip()}\n{"^" * 100}')

    service = json.loads(proc.stdout.decode())
    return service['latest_deployment_id']


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--app-name', required=True,
                        help='Name of the Koyeb app to create')
    parser.add_argument('--service-name', required=True,
                        help='Name of the Koyeb service to create and deploy')
    args = parser.parse_args()

    deployment_id = koyeb_get_last_deployment_id(
        app_name=args.app_name,
        service_name=args.service_name,
    )
    print(f'deployment-id={deployment_id}')


if __name__ == '__main__':
    main()
