# Koyeb Deploy GitHub Action

This action builds and deploys an application from a GitHub repository to Koyeb.

## Usage

Before you can use the Koyeb Deploy Action, you first need to install and configure the Koyeb CLI.

```yaml
- name: Install and configure the Koyeb CLI
  uses: koyeb-community/install-koyeb-cli@v2
  with:
    api_token: "${{ secrets.KOYEB_API_TOKEN }}"
```

Make sure to [set the `KOYEB_API_TOKEN` secret in your repository](https://docs.github.com/en/actions/security-guides/encrypted-secrets). To generate a Koyeb token, go to the [**API access tokens** settings in the Koyeb control panel](https://app.koyeb.com/settings/api).

After the step that installs the Koyeb CLI, add the following step to your workflow:

```yaml
- name: Build and deploy the application to Koyeb
  uses: koyeb/action-git-deploy@v1
  with:
    service-env: "PORT=8000"
    service-ports: "8000:http"
    service-routes: "/:8000"
```

The `service-env`, `service-ports`, and `service-routes` parameters are optional, but should match the needs of your application.  The defaults provided are unlikely to work for most applications.

## Optional Parameters

The following optional parameters can be added to the `with` block:

| Name                      | Description                                                                                                      | Default Value
|---------------------------|------------------------------------------------------------------------------------------------------------------|--
| `app-name`                | The name of the application                                                                                      | `<repo>-<branch>`
| `service-name`            | Name of the Koyeb service to be created                                                                          | `${{ github.ref_name }}`
| `build-timeout`           | Number of seconds to wait for the build before timing out and failing                                            | `900` (15 min)
| `healthy-timeout`         | Number of seconds to wait for the service to become healthy before timing out and failing                        | `900` (15 min)
| `service-env`             | A comma-separated list of KEY=value pairs to set environment variables for the service                           | No env
| `service-instance-type`   | The type of instance to use to run the service                                                                   | `nano`
| `service-regions`         | A comma-separated list of region identifiers to specify where the service should be deployed                     | `fra`
| `service-ports`           | A comma-separated list of port:protocol pairs to specify the ports and protocols to expose for the service       | `80:http`
| `service-routes`          | A comma-separated list of `<path>:<port>` pairs to specify the routes to expose for the service                  | `/:80`
| `service-checks`          | A comma-separated list of `<port>:http:<path>` or `<port>:tcp` pairs to specify the healthchecks for the service | No healthchecks
| `privileged`              | Whether to run the service in privileged mode                                                                    | `false`

If you want to deploy a GitHub repository, you can also add the following parameters:

| Name                | Description                               | Default Value
|---------------------|-------------------------------------------|--
| `git-url`           | The URL of the GitHub repository to build | `github.com/<organization>/<repo>`
| `git-workdir`       | Directory inside the repository to clone  | Empty string, which represents the root directory
| `git-branch`        | The Git branch to deploy                  | `${{ github.ref_name }}`

If you want your GitHub repository to use the default buildpack builder, set the parameter `git-builder` to `buildpack`. You can also add:

| Name                | Description                      | Default Value
|---------------------|----------------------------------|--
| `git-build-command` | Command to build the application | Empty string
| `git-run-command`   | Command to run the application   | Empty string


If instead you want your GitHub repository to use the docker builder, set the parameter `git-builder` to `docker`. You can also add:

| Name                    | Description            | Default Value | Example
|-------------------------|------------------------|---------------|--
| `git-docker-command`    | Docker CMD             | Empty string  | `'nginx -g \"daemon off;\"'`
| `git-docker-dockerfile` | Dockerfile to build    | `Dockerfile`  |
| `git-docker-entrypoint` | Docker ENTRYPOINT      | Empty string  | `/docker-entrypoint.sh`
| `git-docker-target`     | Docker target to build | Empty string  |

If you want to deploy a Docker image and not a GitHub repository, you can set the following parameters:

| Name                             | Description                                    | Default Value | Example
|----------------------------------|------------------------------------------------|---------------|--
| `docker`                         | The docker image to deploy                     | Empty string  |
| `docker-entrypoint`              | Docker ENTRYPOINT                              | Empty string  | `'nginx -g \"daemon off;\"'`
| `docker-command`                 | Docker CMD                                     | Empty string  | `/docker-entrypoint.sh`
| `docker-private-registry-secret` | Secret to authenticate to the private registry | Empty string  |


## Example: deploying a service to Koyeb

```yaml
name: Deploy to Koyeb

on:
  push:
    branches:
      - '*'

jobs:
  deploy:
    runs-on: ubuntu-latest
    concurrency:
      group: "${{ github.ref_name }}"
      cancel-in-progress: true
    steps:
      - name: Install and configure the Koyeb CLI
        uses: koyeb-community/install-koyeb-cli@v2
        with:
          api_token: "${{ secrets.KOYEB_API_TOKEN }}"

      - name: Build and deploy the application to Koyeb
        uses: koyeb/action-git-deploy@v1
        with:
          app-name: my-koyeb-app
          service-name: my-koyeb-service
          service-env: FOO=bar,BAZ=qux
          service-ports: "80:http,8080:http"
          service-routes: "/api:80,/docs:8080"
          service-checks: "8000:http:/,8001:tcp"
```

## Use secrets

Previously, we showed how to configure environment variables for your projects. For secrets variables, you can first create a Koyeb secret with the [`action-git-deploy/secret` action](https://github.com/koyeb/action-git-deploy/blob/master/secret/action.yaml):

```yaml
- name: Create application secret
  uses: koyeb/action-git-deploy/secret@v1
  with:
    secret-name: MY_SECRET
    secret-value: "${{ secrets.DATABASE_URL }}"
```

Afterwards, you can use this secret as an environment variable for your service:

```yaml
- name: Build and deploy the application to Koyeb
  uses: koyeb/action-git-deploy@v1
  with:
    [...]
    service-env: ENV_VAR=@MY_SECRET
```

## Cleaning up Services

After deploying a service to Koyeb, you may want to remove it when it is no longer needed. To do this, you can use the [`koyeb/action-git-deploy/cleanup` action](https://github.com/koyeb/action-git-deploy/blob/master/cleanup/action.yaml). Here's an example of how to use this action:

```yaml
- name: Install and configure the Koyeb CLI
  uses: koyeb-community/install-koyeb-cli@v2
  with:
    api_token: "${{ secrets.KOYEB_API_TOKEN }}"

- name: Clean up Koyeb Service
  uses: koyeb/action-git-deploy/cleanup@v1
```

The first step installs the CLI, which is required to remove the service. The second step performs the cleanup. Optionally, you can provide the `app-name` parameter (which defaults to `<repo>/<branch>`) to specify the name of the application to remove.

### Example: removing a service when a ref is deleted

To remove a Koyeb service when a branch or tag is deleted, you can use the delete event in your workflow file. Here's an example of how to do this:

```yaml
name: Cleanup Koyeb application

on:
  delete:
    branches:
      - '*'

jobs:
  cleanup:
    runs-on: ubuntu-latest
    steps:
      - name: Install and configure the Koyeb CLI
        uses: koyeb-community/install-koyeb-cli@v2
        with:
          api_token: "${{ secrets.KOYEB_API_TOKEN }}"

      - name: Cleanup Koyeb application
        uses: koyeb/action-git-deploy/cleanup@v1
```

In this example, the workflow listens for any branch or tag that is deleted using the `'*'` wildcard. When a delete event occurs, the cleanup job runs and uses the `koyeb/action-git-deploy/cleanup` action to remove the corresponding Koyeb service. Be sure to set `KOYEB_API_TOKEN` as a repository secret.
