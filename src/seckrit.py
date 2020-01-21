#!/usr/bin/env python3

import argparse
import cerberus
import json
import os
import yaml
from google.cloud import secretmanager_v1beta1
from google.oauth2 import service_account


def main(args):
    try:
        # Load and validate the YAML file that tells us which secrets we want to load.
        manifest = load_valid_manifest(args.manifest_file)

        # Create the GCP Secret Manager client using the default credential provider chain.
        client = secretmanager_v1beta1.SecretManagerServiceClient()
        project = client.project_path(manifest["gcp_project_id"])

        # Prepare paths to write a file containing environment variables.
        create_parent_dirs(manifest["environment_file"])
        with open(manifest["environment_file"], "w+") as environment_file:
            # Load each secret specified in the YAML file.
            for secret_info in manifest["secrets"]:
                latest_version = client.secret_version_path(manifest["gcp_project_id"], secret_info["name"], "latest")
                secret = client.access_secret_version(latest_version).payload.data
                secret_type = secret_info["type"]

                if secret_type == "environment_variable":
                    # Add environment secrets to the environment file.
                    print("Adding environment variable {} to {}".format(secret_info["destination"], manifest["environment_file"]))
                    environment_file.write("{}={}\n".format(secret_info["destination"], secret.decode("utf-8")))
                elif secret_type == "file":
                    # Write file secrets to their own dedicated files.
                    destination = secret_info["destination"]
                    print("Writing file '{}'".format(destination))
                    create_parent_dirs(destination)
                    with open(destination, "wb+") as output_file:
                        output_file.write(secret)
                else:
                    raise RuntimeError("Unsupported secret type: {}".format(secret_type))

    except Exception as e:
        print("{}: {}".format(type(e).__name__, e))
        exit(1)


def create_parent_dirs(path):
    """
    Creates parent directories for the given path
    so that files can be written there.
    """
    os.makedirs(os.path.dirname(path), exist_ok=True)


def load_valid_manifest(path):
    """
    Loads and validates the YAML manifest at the given path,
    returning a dictionary containing instructions for returning secrets.
    """
    # Load the manifest file.
    with open(path) as manifest_file:
        manifest = yaml.safe_load(manifest_file)

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
    parser = argparse.ArgumentParser(description="Fetches secrets from Google Cloud Secret Manager according to a YAML manifest.")
    parser.add_argument("manifest_file", metavar="MANIFEST_FILE", help="YAML manifest file specifying which secrets to fetch and how they should be treated.")
    main(parser.parse_args())
