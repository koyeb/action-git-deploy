#!/usr/bin/env python

import argparse
import json
import subprocess


def koyeb_app_get(app_name):
    """Wrapper around koyeb CLI to get application. Assumes that the koyeb CLI
    is installed and configured."""
    proc = subprocess.run(
        ['koyeb', 'app', 'get', app_name, '-o', 'json'],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )

    # Success
    if proc.returncode != 0:
        stderr = proc.stderr.decode()
        raise RuntimeError(
            f'Error while creating the application {app_name}\n{"v" * 100}\n{stderr.strip()}\n{"^" * 100}'
        )

    return json.loads(proc.stdout.decode())


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--app-name', required=True,
                        help='Name of the Koyeb app to create')
    args = parser.parse_args()

    config = koyeb_app_get(args.app_name)
    for domain in config['domains']:
        print(f"Your application is available at: {domain['name']}")


if __name__ == '__main__':
    main()
