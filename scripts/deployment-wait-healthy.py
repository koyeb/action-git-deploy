#!/usr/bin/env python

import argparse
import json
import subprocess
import sys
import time


def koyeb_get_deployment_info(deployment_id):
    proc = subprocess.run([
        'koyeb', 'deployments', 'get', deployment_id,
        '-o', 'json'
    ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    if proc.returncode != 0:
        stderr = proc.stderr.decode()
        raise RuntimeError(
            f'Error while getting info of deployment {deployment_id}\n{"v" * 100}\n{stderr.strip()}\n{"^" * 100}')

    deployment = json.loads(proc.stdout.decode())
    return deployment


def koyeb_wait_healthy(*, deployment_id, timeout):
    start_time = time.time()
    previous_status = None
    i = 0
    while True:
        info = koyeb_get_deployment_info(deployment_id)
        if info['status'] != previous_status:
            print(f'>>>> Deployment status is {info["status"]}')
            previous_status = info['status']

        if info['status'] == 'HEALTHY':
            break
        elif info['status'] in ('CANCELING', 'CANCELED', 'STOPPING', 'STOPPED', 'ERRORING', 'ERROR'):
            raise RuntimeError(
                f'Deployment {deployment_id} is in status {info["status"]}.'
            )

        if time.time() - start_time > timeout:
            raise RuntimeError(
                f'Timeout reached while waiting for deployment {deployment_id} to be healthy'
            )

        if i and i % 10 == 0:
            elapsed = int(time.time() - start_time)
            print(
                f'[{elapsed}s] Still waiting for deployment {deployment_id} to be healthy. Currently in status {info["status"]}.'
            )

        time.sleep(3)
        i += 1


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--deployment-id', required=True,
                        help='ID of the Koyeb deployment to follow')
    parser.add_argument('--timeout', required=False, type=float, default=60 * 30,  # 30 minutes
                        help='Raise an error if the deployment is not healthy after this timeout')
    args = parser.parse_args()

    koyeb_wait_healthy(deployment_id=args.deployment_id, timeout=args.timeout)


if __name__ == '__main__':
    main()
