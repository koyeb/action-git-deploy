#!/usr/bin/env python

import argparse
import subprocess


class KoyebSecretAlreadyExists(Exception):
    pass


def koyeb_secret_create(*, secret_name, secret_value):
    """Wrapper around koyeb CLI to create a secret. If the service already
    exists, it raises an error. Assumes that the koyeb CLI is installed and
    configured."""
    args = [
        'koyeb', 'secret', 'create',
        secret_name,
        '--value', secret_value,
    ]
    args += ['-o', 'json', '-d']

    proc = subprocess.run(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    if proc.returncode != 0:
        # If the secret already exists, koyeb-cli displays an error containing the
        # strings "400 Bad request" and "Name already exists".
        stderr = proc.stderr.decode()
        if '400 Bad request'.lower() in stderr.lower() and 'already exists' in stderr.lower():
            raise KoyebSecretAlreadyExists(
                f'Secret {secret_name} already exists. Skip.')
        raise RuntimeError(
            f'Error while creating the service {secret_name}\n{"v" * 100}\n{stderr.strip()}\n{"^" * 100}')


def koyeb_secret_update(*, secret_name, secret_value):
    """Wrapper around koyeb CLI to update the definition of an existing secret.
    Assumes that the koyeb CLI is installed and configured."""
    args = [
        'koyeb', 'secret', 'update',
        secret_name,
        '--value', secret_value,
    ]
    args += ['-o', 'json']

    proc = subprocess.run(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    if proc.returncode != 0:
        stderr = proc.stderr.decode()
        raise RuntimeError(
            f'Error while updating the secret {secret_name}\n{"v" * 100}\n{stderr.strip()}\n{"^" * 100}')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--secret-name', required=True,
                        help='Name of the Koyeb secret to create')
    parser.add_argument('--secret-value', required=True,
                        help='Value of the Koyeb secret to create')
    args = parser.parse_args()

    try:
        koyeb_secret_create(**vars(args))
    except KoyebSecretAlreadyExists:
        print('Secret already exists. Triggering an update instead.')
        koyeb_secret_update(**vars(args))


if __name__ == '__main__':
    main()
