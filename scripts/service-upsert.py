#!/usr/bin/env python

import argparse
import subprocess


def argparse_to_env(value):
    env = []

    for part in value.split(','):
        if not part:
            continue

        split = part.split('=')
        name = split[0]
        value = '='.join(split[1:])

        env.append({'name': name, 'value': value})
    return env


def argparse_to_ports(value):
    errmsg = 'should be formed as <port>:http or <port>:http2 separated by commas'
    ports = []

    for r in value.split(','):
        if not r:
            continue

        try:
            port, protocol = r.split(':')
        except ValueError:
            raise argparse.ArgumentTypeError(errmsg)

        if protocol not in ('http', 'http2'):
            raise argparse.ArgumentTypeError(
                f'{errmsg} and "{protocol}" is not a valid protocol')

        ports.append({'port': port, 'protocol': protocol})
    return ports


def argparse_to_routes(value):
    errmsg = 'should be formed as <PATH>:<port> separated by commas'
    routes = []

    for r in value.split(','):
        if not r:
            continue

        try:
            path, port = r.split(':')
        except ValueError:
            raise argparse.ArgumentTypeError(errmsg)

        try:
            port = int(port)
        except ValueError:
            raise argparse.ArgumentTypeError(
                f'{errmsg} and "{port}" is not a valid port')

        routes.append({'path': path, 'port': port})
    return routes


class KoyebServiceAlreadyExists(Exception):
    pass


def koyeb_service_create(*, app_name, service_name, git_url, git_workdir, git_branch, service_env, service_ports, service_routes):
    """Wrapper around koyeb CLI to create a service. If the service already
    exists, it raises an error. Assumes that the koyeb CLI is installed and
    configured."""
    args = [
        'koyeb', 'service', 'create',
        service_name,
        '--app', app_name,
        '--git', git_url,
        '--git-workdir', git_workdir,
        '--git-branch', git_branch,
    ]
    for env in service_env:
        args += ['--env', f'{env["name"]}={env["value"]}']
    for port in service_ports:
        args += ['--ports', f'{port["port"]}:{port["protocol"]}']
    for route in service_routes:
        args += ['--routes', f'{route["path"]}:{route["port"]}']

    args += ['-o', 'json', '-d']

    proc = subprocess.run(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    if proc.returncode != 0:
        stderr = proc.stderr.decode()
        if '400 Bad request'.lower() in stderr.lower():
            raise KoyebServiceAlreadyExists(
                f'Service {service_name} already exists. Skip.')
        raise RuntimeError(
            f'Error while creating the service {service_name}\n{"v" * 100}\n{stderr.strip()}\n{"^" * 100}')


def koyeb_service_update(*, app_name, service_name, git_url, git_workdir, git_branch, service_env, service_ports, service_routes):
    """Wrapper around koyeb CLI to update the definition of an existing service.
    Assumes that the koyeb CLI is installed and configured."""
    args = [
        'koyeb', 'service', 'update',
        f'{app_name}/{service_name}',
        '--git', git_url,
        '--git-workdir', git_workdir,
        '--git-branch', git_branch,
    ]
    for env in service_env:
        args += ['--env', f'{env["name"]}={env["value"]}']
    for port in service_ports:
        args += ['--ports', f'{port["port"]}:{port["protocol"]}']
    for route in service_routes:
        args += ['--routes', f'{route["path"]}:{route["port"]}']

    args += ['-o', 'json']

    proc = subprocess.run(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    if proc.returncode != 0:
        stderr = proc.stderr.decode()
        if '400 Bad request'.lower() in stderr.lower():
            raise KoyebServiceAlreadyExists(
                f'Service {service_name} already exists. Skip.')
        raise RuntimeError(
            f'Error while updating the service {service_name}\n{"v" * 100}\n{stderr.strip()}\n{"^" * 100}')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--app-name', required=True,
                        help='Name of the Koyeb app to create')
    parser.add_argument('--service-name', required=True,
                        help='Name of the Koyeb service to create and deploy')
    parser.add_argument('--git-url', required=True,
                        help='URL of the GIT repository to deploy')
    parser.add_argument('--git-workdir', required=True,
                        help='Workdir, if the application to build is not in the root directory of the repository')
    parser.add_argument('--git-branch', required=True,
                        help='GIT branch to deploy')
    parser.add_argument('--service-env', required=True,
                        help='Comma separated list of <KEY>=<value> to specify the application environment',
                        type=argparse_to_env)
    parser.add_argument('--service-ports', required=True,
                        help='Comma separated list of <KEY>=<value> to specify the ports to expose',
                        type=argparse_to_ports)
    parser.add_argument('--service-routes', required=True,
                        help='Comma separated list of <PATH>:<port> to specify the routes to expose',
                        type=argparse_to_routes)
    args = parser.parse_args()

    try:
        koyeb_service_create(**vars(args))
    except KoyebServiceAlreadyExists:
        print('Service already exists. Triggering an update instead.')
        koyeb_service_update(**vars(args))


if __name__ == '__main__':
    main()
