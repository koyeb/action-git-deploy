#!/usr/bin/env python

import argparse
import json
import subprocess


def koyeb_app_create(app_name):
    """Wrapper around koyeb CLI to create an app. If the app already exists, it
    does nothing. Assumes that the koyeb CLI is installed and configured."""
    proc = subprocess.run(
        ['koyeb', 'app', 'create', app_name, '-o', 'json', '-d'],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )

    # Success
    if proc.returncode == 0:
        response = json.loads(proc.stdout.decode())
        print(
            f'App {app_name} successfully created. Output:\n{"v" * 100}\n{json.dumps(response, indent=2)}\n{"^" * 100}')
        return

    # If the app already exists, koyeb-cli displays an error containing the
    # strings "400 Bad request" and "Name already exists".
    stderr = proc.stderr.decode()
    if '400 Bad request'.lower() in stderr.lower() and 'already exists' in stderr.lower():
        print(f'App {app_name} already exists. Skip.')
        return

    raise RuntimeError(
        f'Error while creating the application {app_name}\n{"v" * 100}\n{stderr.strip()}\n{"^" * 100}'
    )


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--app-name', required=True,
                        help='Name of the Koyeb app to create')
    args = parser.parse_args()

    koyeb_app_create(args.app_name)


if __name__ == '__main__':
    main()
