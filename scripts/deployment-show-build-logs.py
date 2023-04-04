#!/usr/bin/env python

import argparse
import json
import select
import subprocess
import sys
import threading


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


class DeploymentStatus:
    def __init__(self, deployment_id):
        self.deployment_id = deployment_id
        self.status = None

    def check(self):
        """Called every few seconds to check the deployment status. Returns True if we
        are no longer in the building phase."""
        deployment_info = koyeb_get_deployment_info(self.deployment_id)
        deployment_status = deployment_info['status']

        old_status = self.status
        self.status = deployment_status

        if deployment_status not in ('PENDING', 'PROVISIONING'):
            print(
                f'>>>> Deployment status is {deployment_status}. Stop following build logs.'
            )
            return True
        elif deployment_status != old_status:
            print(f'>>>> Deployment status is {deployment_status}')
            return False


def timeout_callback(proc):
    sys.stderr.write('Timeout reached, killing the process...\n')
    proc.kill()


def koyeb_build_logs(deployment_id, timeout, tick_func):
    """This function is a generator that yields the build logs line by line. Assumes
    that the koyeb CLI is installed and configured. Exits when the build is
    finished. Every few seconds, the tick_func is called to check the deployment
    status. If it returns True, the generator exits.
    """
    proc = subprocess.Popen([
        'koyeb', 'deployment', 'logs', deployment_id, '-t', 'build'
    ], stdout=subprocess.PIPE, stderr=subprocess.PIPE, bufsize=0)

    timer = threading.Timer(timeout, timeout_callback, [proc])
    timer.start()

    while True:
        ready_to_read, _, _ = select.select([proc.stdout], [], [], 3)

        # Timeout reached and nothing to read: call the tick function
        if not ready_to_read:
            if tick_func():
                timer.cancel()
                proc.kill()
                return
            continue

        line = proc.stdout.readline()
        if not line:
            timer.cancel()
            proc.kill()
            return

        yield line


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--deployment-id', required=True,
                        help='ID of the Koyeb deployment to follow')
    parser.add_argument('--timeout', required=False, type=int, default=60 * 15,  # 15 minutes
                        help='If the deployment is still building after this timeout, the process will exit with an error')
    args = parser.parse_args()

    for line in koyeb_build_logs(args.deployment_id, args.timeout, DeploymentStatus(args.deployment_id).check):
        sys.stdout.buffer.write(line)
        sys.stdout.buffer.flush()


if __name__ == '__main__':
    main()
