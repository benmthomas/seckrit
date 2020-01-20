#!/usr/bin/env python3

import argparse
import cerberus
import json
import os
import yaml
from google.cloud import secretmanager_v1beta1
from google.oauth2 import service_account


def main(args):

    # Load the YAML file that tells us which secrets we want to load (and what to do with them).
    if args.manifest:
        manifest = load_manifest_from_file(args.manifest)
    elif "SECKRIT_MANIFEST" in os.environ:
        manifest = load_manifest_from_string()
    else:
        raise RuntimeError("Should pass --manifest argument or define SECKRIT_MANIFEST environment variable")

    # Create the GCP Secret Manager client using the default credential provider chain.
    credentials_string = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS_JSON")
    if credentials_string is not None:
        credentials_json = json.loads(credentials_string)
        credentials = service_account.Credentials.from_service_account_info(credentials_json)
        client = secretmanager_v1beta1.SecretManagerServiceClient(credentials=credentials)
    else:
        client = secretmanager_v1beta1.SecretManagerServiceClient()
    project = client.project_path(manifest["gcp_project_id"])

    # Prepare paths to write a file containing environment variables.
    try:
        create_parent_dirs(manifest["environment_file"])
        environment_file = open(manifest["environment_file"], "w+")
    except PermissionError as e:
        print("ERROR: Permission denied: {}".format(manifest["environment_file"]))
        exit(1)

    # Load each secret specified in the YAML file.
    for secret_info in manifest["secrets"]:
        latest_version = client.secret_version_path(manifest["gcp_project_id"], secret_info["name"], "latest")
        secret = client.access_secret_version(latest_version).payload.data
        secret_type = secret_info["type"]

        if secret_type == "environment_variable":
            print(
                "Adding environment variable {} to {}".format(secret_info["destination"], manifest["environment_file"]))
            environment_file.write("{}={}\n".format(secret_info["destination"], secret.decode("utf-8")))
        elif secret_type == "file":
            destination = secret_info["destination"]
            print("Writing file '{}'".format(destination))

            try:
                create_parent_dirs(destination)
                with open(destination, "wb+") as output_file:
                    output_file.write(secret)
            except PermissionError as e:
                print("Permission denied: {}".format(destination))
        else:
            print("Unsupported type: {}".format(secret_type))

    environment_file.close()


def create_parent_dirs(path):
    """
    Creates parent directories for the given path
    so that files can be written there.
    """
    os.makedirs(os.path.dirname(path), exist_ok=True)


def load_manifest_from_file(path):
    """
    Loads the YAML manifest at the given path,
    sends the YAML for validation and returns the result.
    """
    # Load the manifest file.
    with open(path) as manifest_file:
        manifest = yaml.safe_load(manifest_file)
    return validate_manifest(manifest)


def load_manifest_from_string():
    """
    Loads the YAML manifest from the environment variable,
    sends the YAML for validation and returns the result.
    """
    manifest = yaml.safe_load(os.environ.get('SECKRIT_MANIFEST'))
    return validate_manifest(manifest)


def validate_manifest(manifest):
    """
    Validates the YAML manifest being passed as argument,
    returning a dictionary containing instructions for returning secrets
    """
    # Load the schema for validating the manifest file.
    script_path = os.path.dirname(os.path.realpath(__file__))
    schema_path = os.path.join(script_path, "manifest_schema.yml")
    with open(schema_path) as schema_file:
        schema = yaml.safe_load(schema_file)

    # Validate the manifest using the schema.
    validator = cerberus.Validator(schema)
    if not validator.validate(manifest, schema):
        print("Errors encountered when parsing manifest file:\n")
        print(yaml.dump(validator.errors, allow_unicode=True, default_flow_style=False))
        exit(1)

    return validator.normalized(manifest)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Fetches secrets from Google Cloud Secret Manager according to a YAML manifest.")
    parser.add_argument("--manifest", metavar="MANIFEST_FILE",
                        help="YAML manifest file specifying which secrets to fetch and how they should be treated.")
    main(parser.parse_args())
