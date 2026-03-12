#!/usr/bin/env python

import argparse
import shlex
import subprocess


def argparse_to_subprocess_params(value):
    """Given a string (e.g. 'cat -te "superfile with spaces.txt"), returns a
    list of params that can be passed to subprocess."""
    return shlex.split(value)


def argparse_to_regions(value):
    regions = []

    for part in value.split(','):
        if not part:
            continue

        regions.append(part)
    return regions


def argparse_to_csv_list(value):
    values = []

    for part in value.split(','):
        if not part:
            continue

        values.append(part)
    return values


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

        if protocol not in ('http', 'http2', 'tcp'):
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


def argparse_to_healthchecks(value):
    errmsg = 'should be formed as <port>:http:<path> or <port>:tcp separated by commas'
    healthchecks = []

    for r in value.split(','):
        if not r:
            continue

        parts = r.split(':')

        if (
            len(parts) not in (2, 3)
            or (len(parts) == 2 and parts[1] != 'tcp')
            or (len(parts) == 3 and parts[1] != 'http')
        ):
            raise argparse.ArgumentTypeError(errmsg)

        try:
            port = int(parts[0])
        except ValueError:
            raise argparse.ArgumentTypeError(
                f'{errmsg} and "{port}" is not a valid port')

        if parts[1] == 'http':
            healthchecks.append(
                {'port': port, 'protocol': 'http', 'path': parts[2]}
            )
        else:
            healthchecks.append({'port': port, 'protocol': 'tcp'})
    return healthchecks


def argparse_to_bool(value):
    if isinstance(value, bool):
        return value
    if value.lower() in ('yes', 'true', 't', 'y', '1'):
        return True
    elif value.lower() in ('no', 'false', 'f', 'n', '0'):
        return False
    else:
        raise argparse.ArgumentTypeError('Boolean value expected.')


def argparse_to_optional_int(value):
    if value in (None, ''):
        return None

    try:
        return int(value)
    except ValueError:
        raise argparse.ArgumentTypeError('Integer value expected.')


def argparse_to_deployment_strategy(value):
    if value in (None, ''):
        return None

    valid = ('rolling', 'blue-green', 'immediate')
    if value not in valid:
        raise argparse.ArgumentTypeError(
            f'Deployment strategy must be one of {", ".join(valid)}.'
        )
    return value


def service_common_args(
    *,
    service_instance_type, service_regions, service_env, service_ports, service_routes, service_checks, service_type,
    service_checks_grace_period, service_proxy_ports, service_volumes,
    service_scale, service_min_scale, service_max_scale,
    service_autoscaling_average_cpu, service_autoscaling_average_mem,
    service_autoscaling_concurrent_requests, service_autoscaling_requests_per_second,
    service_autoscaling_requests_response_time,
    service_deployment_strategy,
    service_light_sleep_delay, service_deep_sleep_delay,
    service_delete_after_delay, service_delete_after_inactivity_delay,
    docker, docker_entrypoint, docker_command, docker_private_registry_secret,
    git_url, git_workdir, git_branch, git_sha,
    git_build_command, git_run_command,
    git_builder,
    git_docker_command, git_docker_dockerfile, git_docker_entrypoint, git_docker_target,
    privileged, skip_cache,
    **kwargs
):
    """Arguments common to service create and service update."""
    params = []

    if docker:
        params += [
            '--docker', docker,
        ]
        if not docker_entrypoint:
            params += ['--docker-entrypoint', '']
        else:
            for part in docker_entrypoint:
                params += ['--docker-entrypoint', part]
        if not docker_command:  # erase existing command and args
            params += ['--docker-command', '']
            params += ['--docker-args', '']
        else:
            params += ['--docker-command', docker_command[0]]
            for part in docker_command[1:]:
                params += ['--docker-args', part]
        params += [
            '--docker-private-registry-secret', docker_private_registry_secret
        ]

    else:
        params += ['--git', git_url]
        if git_workdir is not None:
            params += ['--git-workdir', git_workdir]
        if git_branch:
            params += ['--git-branch', git_branch]
        if git_sha:
            params += ['--git-sha', git_sha]
        params += ['--git-no-deploy-on-push']
        if git_builder == 'buildpack':
            params += ['--git-builder', 'buildpack']
            if git_build_command is not None:
                params += ['--git-buildpack-build-command', git_build_command]
            if git_run_command is not None:
                params += ['--git-buildpack-run-command', git_run_command]
        else:
            params += ['--git-builder', 'docker']
            if not git_docker_command:  # erase existing command and args
                params += ['--git-docker-command', '']
                params += ['--git-docker-args', '']
            else:
                params += ['--git-docker-command', git_docker_command[0]]
                for part in git_docker_command[1:]:
                    params += ['--git-docker-args', part]
            if git_docker_dockerfile is not None:
                params += ['--git-docker-dockerfile', git_docker_dockerfile]
            if git_docker_target is not None:
                params += ['--git-docker-target', git_docker_target]
            if not git_docker_entrypoint:
                params += ['--git-docker-entrypoint', '']
            else:
                for part in git_docker_entrypoint:
                    params += ['--git-docker-entrypoint', part]

    params += ['--type', service_type]
    params += ['--instance-type', service_instance_type]
    for region in service_regions:
        params += ['--regions', region]
    for env in service_env:
        params += ['--env', f'{env["name"]}={env["value"]}']
    for port in service_ports:
        params += ['--ports', f'{port["port"]}:{port["protocol"]}']
    for route in service_routes:
        params += ['--routes', f'{route["path"]}:{route["port"]}']
    for check in service_checks:
        params += [
            '--checks',
            f'{check["port"]}:{check["protocol"]}:{check["path"]}' if check["protocol"] == 'http' else f'{check["port"]}:{check["protocol"]}'
        ]
    for grace_period in service_checks_grace_period:
        params += ['--checks-grace-period', grace_period]
    for proxy_port in service_proxy_ports:
        params += ['--proxy-ports', proxy_port]
    for volume in service_volumes:
        params += ['--volumes', volume]

    if service_scale is not None:
        params += ['--scale', str(service_scale)]
    if service_min_scale is not None:
        params += ['--min-scale', str(service_min_scale)]
    if service_max_scale is not None:
        params += ['--max-scale', str(service_max_scale)]

    if service_autoscaling_average_cpu is not None:
        params += ['--autoscaling-average-cpu', str(service_autoscaling_average_cpu)]
    if service_autoscaling_average_mem is not None:
        params += ['--autoscaling-average-mem', str(service_autoscaling_average_mem)]
    if service_autoscaling_concurrent_requests is not None:
        params += ['--autoscaling-concurrent-requests', str(service_autoscaling_concurrent_requests)]
    if service_autoscaling_requests_per_second is not None:
        params += ['--autoscaling-requests-per-second', str(service_autoscaling_requests_per_second)]
    if service_autoscaling_requests_response_time is not None:
        params += ['--autoscaling-requests-response-time', str(service_autoscaling_requests_response_time)]

    if service_deployment_strategy:
        params += ['--deployment-strategy', service_deployment_strategy]
    if service_light_sleep_delay:
        params += ['--light-sleep-delay', service_light_sleep_delay]
    if service_deep_sleep_delay:
        params += ['--deep-sleep-delay', service_deep_sleep_delay]
    if service_delete_after_delay:
        params += ['--delete-after-delay', service_delete_after_delay]
    if service_delete_after_inactivity_delay:
        params += ['--delete-after-inactivity-delay', service_delete_after_inactivity_delay]

    params += [f'--privileged={"true" if privileged else "false"}']
    params += [f'--skip-cache={"true" if skip_cache else "false"}']
    return params


def koyeb_service_exists(app_name, service_name):
    """Wrapper around the koyeb CLI which returns True if a service exists."""
    args = [
        'koyeb', 'services', 'get',
        service_name,
        '--app', app_name,
        '-o', 'json',
    ]
    print(f'>> {" ".join(shlex.quote(arg) for arg in args)}')
    proc = subprocess.run(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    return proc.returncode == 0


def koyeb_service_create(app_name, service_name, params):
    """Wrapper around koyeb CLI to create a service. If the service already
    exists, it raises an error. Assumes that the koyeb CLI is installed and
    configured."""
    args = [
        'koyeb', 'services', 'create',
        service_name,
        '--app', app_name,
        '-o', 'json',
    ] + params

    print(f'>> {" ".join(shlex.quote(arg) for arg in args)}')

    proc = subprocess.run(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    if proc.returncode != 0:
        stderr = proc.stderr.decode()
        raise RuntimeError(
            f'Error while creating the service {service_name}\n{"v" * 100}\n{stderr.strip()}\n{"^" * 100}'
        )


def koyeb_service_update(app_name, service_name, params):
    """Wrapper around koyeb CLI to update the definition of an existing service.
    Assumes that the koyeb CLI is installed and configured."""
    args = [
        'koyeb', 'services', 'update',
        f'{app_name}/{service_name}',
        '-o', 'json'
    ] + params

    print(f'>> {" ".join(shlex.quote(arg) for arg in args)}')
    proc = subprocess.run(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    if proc.returncode != 0:
        stderr = proc.stderr.decode()
        raise RuntimeError(
            f'Error while updating the service {service_name}\n{"v" * 100}\n{stderr.strip()}\n{"^" * 100}'
        )


def check_mutual_exclusive_options(parser, args):
    has_docker_source = bool(args.docker)
    has_git_source = bool(args.git_url)

    if has_docker_source == has_git_source:
        parser.error(
            'Set exactly one deployment source: --docker or --git-url.'
        )

    if has_docker_source and any([
        args.git_workdir,
        args.git_branch,
        args.git_sha,
        args.git_builder,
        args.git_build_command,
        args.git_run_command,
        args.git_docker_command,
        args.git_docker_dockerfile,
        args.git_docker_entrypoint,
        args.git_docker_target,
    ]):
        parser.error(
            'Docker and GIT options are mutually exclusive. Set either --docker-* or --git-* options, not both.')

    if has_git_source and any([
        args.docker_entrypoint,
        args.docker_command,
        args.docker_private_registry_secret,
    ]):
        parser.error(
            'Docker and GIT options are mutually exclusive. Set either --docker-* or --git-* options, not both.'
        )

    git_builder = args.git_builder or 'buildpack'

    if git_builder == 'docker' and (
        args.git_build_command or
        args.git_run_command
    ):
        parser.error(
            '--git-build-command and --git-run-command are only valid with the buildpack builder.'
        )
    elif git_builder == 'buildpack' and (
        any([True for key, value in vars(args).items()
            if key.startswith('git_docker') and value])
    ):
        parser.error(
            '--git-docker-* arguments are only valid with the docker builder.'
        )


def main():
    parser = argparse.ArgumentParser()

    parser.add_argument('--app-name', required=True,
                        help='Name of the Koyeb app to create')
    parser.add_argument('--service-name', required=True,
                        help='Name of the Koyeb service to create and deploy')
    parser.add_argument("--privileged", type=argparse_to_bool, nargs='?',
                        const=True, default=False,
                        help="Whether to run the container in privileged mode or not")
    parser.add_argument("--skip-cache", type=argparse_to_bool, nargs='?',
                        const=True, default=False,
                        help="Whether to skip the cache when building the application")
    parser.add_argument("--service-type", choices=('web', 'worker', 'sandbox'), required=True, help="Service type")

    # Docker deployment
    parser.add_argument('--docker', required=False,
                        help='Docker image (only for docker deployments)')
    parser.add_argument('--docker-entrypoint', required=False,
                        help='Docker entrypoint (only for docker deployments)',
                        type=argparse_to_subprocess_params)
    parser.add_argument('--docker-command', required=False,
                        help='Docker CMD (only for docker deployments)',
                        type=argparse_to_subprocess_params)
    parser.add_argument('--docker-private-registry-secret', required=False,
                        default='',
                        help='Docker secret in case you are using a private registry (only for docker deployments)')

    # Git deployment
    parser.add_argument('--git-url', required=False,
                        help='URL of the GIT repository to deploy')
    parser.add_argument('--git-workdir', required=False,
                        help='Workdir, if the application to build is not in the root directory of the repository')
    parser.add_argument('--git-branch', required=False,
                        help='GIT branch to deploy')
    parser.add_argument('--git-sha', required=False,
                        help='GIT SHA to deploy')
    parser.add_argument('--git-builder', required=False, default='buildpack', choices=('buildpack', 'docker'),
                        help='Type of builder to use')

    # Git deployment: buildpack builder options
    parser.add_argument('--git-build-command', required=False,
                        help='Command to build the application (only for git deployments with the buildpack builder)')
    parser.add_argument('--git-run-command', required=False,
                        help='Command to run the application (only for git deployments with the buildpack builder)')

    # Git deployment: docker builder options
    parser.add_argument('--git-docker-command', required=False,
                        help='Docker CMD (only for git deployments with the docker builder)',
                        type=argparse_to_subprocess_params)
    parser.add_argument('--git-docker-dockerfile', required=False,
                        help='Dockerfile path (only for git deployments with the docker builder)')
    parser.add_argument('--git-docker-entrypoint', required=False,
                        help='Docker entrypoint (only for git deployments with the docker builder)',
                        type=argparse_to_subprocess_params)
    parser.add_argument('--git-docker-target', required=False,
                        help='Docker target (only for git deployments with the docker builder)')

    # Service options
    parser.add_argument('--service-instance-type', required=True,
                        help='Type of instance to use to run the service')
    parser.add_argument('--service-regions', required=True,
                        help='Comma separated list of region identifiers to specify where the service should be deployed',
                        type=argparse_to_regions)
    parser.add_argument('--service-env', required=True,
                        help='Comma separated list of <KEY>=<value> to specify the application environment',
                        type=argparse_to_env)
    parser.add_argument('--service-ports', required=True,
                        help='Comma separated list of <KEY>=<value> to specify the ports to expose',
                        type=argparse_to_ports)
    parser.add_argument('--service-routes', required=True,
                        help='Comma separated list of <path>:<port> to specify the routes to expose',
                        type=argparse_to_routes)
    parser.add_argument('--service-checks', required=True,
                        help='Comma separated list of <port>:http:<path> or <port>:tcp to specify the service healthchecks',
                        type=argparse_to_healthchecks)
    parser.add_argument('--service-checks-grace-period', required=False, default='',
                        help='Comma separated list of <healthcheck>=<seconds> to specify grace period values for service checks',
                        type=argparse_to_csv_list)
    parser.add_argument('--service-proxy-ports', required=False, default='',
                        help='Comma separated list of <port>[:tcp] to specify proxy ports',
                        type=argparse_to_csv_list)
    parser.add_argument('--service-volumes', required=False, default='',
                        help='Comma separated list of <volume>:<path> to attach service volumes',
                        type=argparse_to_csv_list)
    parser.add_argument('--service-scale', required=False, type=argparse_to_optional_int,
                        help='Set both min and max scale values')
    parser.add_argument('--service-min-scale', required=False, type=argparse_to_optional_int,
                        help='Set minimum number of instances')
    parser.add_argument('--service-max-scale', required=False, type=argparse_to_optional_int,
                        help='Set maximum number of instances')
    parser.add_argument('--service-autoscaling-average-cpu', required=False, type=argparse_to_optional_int,
                        help='Target CPU usage percentage for autoscaling')
    parser.add_argument('--service-autoscaling-average-mem', required=False, type=argparse_to_optional_int,
                        help='Target memory usage percentage for autoscaling')
    parser.add_argument('--service-autoscaling-concurrent-requests', required=False, type=argparse_to_optional_int,
                        help='Target concurrent requests for autoscaling')
    parser.add_argument('--service-autoscaling-requests-per-second', required=False, type=argparse_to_optional_int,
                        help='Target requests per second for autoscaling')
    parser.add_argument('--service-autoscaling-requests-response-time', required=False, type=argparse_to_optional_int,
                        help='Target p95 response time in milliseconds for autoscaling')
    parser.add_argument('--service-deployment-strategy', required=False,
                        type=argparse_to_deployment_strategy,
                        help='Deployment strategy to use')
    parser.add_argument('--service-light-sleep-delay', required=False,
                        help='Delay before entering light sleep (e.g. 1m, 5m, 1h, 0)')
    parser.add_argument('--service-deep-sleep-delay', required=False,
                        help='Delay before entering deep sleep (e.g. 5m, 30m, 1h, 0)')
    parser.add_argument('--service-delete-after-delay', required=False,
                        help='Automatically delete service after this duration (e.g. 1h, 24h, 0)')
    parser.add_argument('--service-delete-after-inactivity-delay', required=False,
                        help='Automatically delete service after inactivity for this duration (e.g. 1h, 24h, 0)')
    args = parser.parse_args()

    check_mutual_exclusive_options(parser, args)

    params = service_common_args(**vars(args))

    if not koyeb_service_exists(args.app_name, args.service_name):
        koyeb_service_create(args.app_name, args.service_name, params)
    else:
         print('Service already exists. Triggering an update.')
         koyeb_service_update(args.app_name, args.service_name, params)


if __name__ == '__main__':
    main()
