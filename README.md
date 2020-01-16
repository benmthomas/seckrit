# Seckrit

> Simple secret management, particularly for Spring Boot applications running on Kubernetes.

Seckrit provides a simple way to fetch secrets from a secret manager and make them available to application servers or Kubernetes pod containers. Secrets can be made available as either environment variables or files.

This eliminates the insecure practice of storing secrets in code repositories, leaving only a single set of credentials to protect (e.g. using the secret management features of your CI/CD provider).

Currently, only Google Cloud Secret Manager is supported, but feel free to submit a pull request to add support for others.

![seckrit.jpg](.github/seckrit.jpg)

## Usage

Seckrit can either be used as a regular Python script on a local machine or application server, or as an `initContainer` in a Kubernetes `Deployment`.

### As a script

1. Write a [manifest file](./example_manifest.yml) that conforms to the [schema](manifest_schema.yml). This file lists the secrets you want to fetch and how they should be made available to the app.
2. Set an environment variable `GOOGLE_APPLICATION_CREDENTIALS` to the location of a GCP service account file. This can be done inline when running the command if you like.
3. Run `python3 seckrit.py /path/to/manifest.yml`.
4. Run `. /path/to/environment && /path/to/your/app`. This will set environment variables before running your app. If you like, you can also delete the environment file after reading it.

### In a Kubernetes Deployment

1. Write a [manifest file](./example_manifest.yml) and embed it in a Kubernetes `ConfigMap`.
2. In your `Deployment`, define an `initContainer` that mounts the manifest `ConfigMap` as a file.
3. Set an environment variable `GOOGLE_APPLICATION_CREDENTIALS` to the value of a Kubernetes `Secret` that contains the service account.
4. Define a named volume to share between the `initContainer` and the `container`. This volume is where secrets will be stored, so it should encompass the paths you used in your manifest file.
5. In the `containers` section, mount the volume containing the secrets fetched by the `initContainer`.
6. Define your `command` as `. /path/to/environment && /path/to/your/app`.

## Getting Started

### Installing Python dependencies

Run `pip3 install --user -r requirements.txt` to install Python dependencies.

### Building the Docker image

Run `docker build -t TAG .`, using a `TAG` of your choosing.

## License

This project is licensed under the [BSD 3-Clause](./LICENSE.md) license.

## Contributing

Contributions are most welcome. Before submitting an issue or pull request, please familiarise yourself with the [Contribution Guidelines](./CONTRIBUTING.md).
