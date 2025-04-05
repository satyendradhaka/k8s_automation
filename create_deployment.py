import json
import subprocess

from utils import runKubectlCommand


def createHelmCommand(**kwargs):
    """
    Create a Helm command with the specified arguments.

    Args:
        **kwargs: Keyword arguments representing Helm command options.

    Returns:
        list: A list representing the Helm command.
    """
    required_keys = ['release_name', 'namespace']
    for key in required_keys:
        if key not in kwargs:
            raise KeyError(f"Missing required key: {key}")

    command = ["helm", "upgrade", "--install"]
    # Define the Helm chart and release name
    chart_name = "automation-chart"
    release_name = kwargs.get('release_name', 'my-release')

    # Add the release name and chart name to the command
    command.append(release_name)
    command.append(chart_name)

    # Add the namespace if provided
    if 'namespace' in kwargs:
        command.append("--namespace")
        command.append(kwargs['namespace'])

    # Add the values file if provided
    if 'values_file' in kwargs:
        command.append("-f")
        command.append(kwargs['values_file'])

    # Add any additional Helm options
    for key, value in kwargs.items():
        if key not in ['namespace', 'release_name', 'values_file']:
            command.append("--set")
            command.append(f"{key}={value}")

    return command


def createDeployment(helmCommand, releaseName, chartName):
    """
    Create a deployment in the Kubernetes cluster using Helm.
    """
    try:
        # Run the Helm command
        subprocess.run(helmCommand, check=True)
        print(f"Deployment '{releaseName}' created successfully using chart '{chartName}'.")
    except subprocess.CalledProcessError as e:
        print(f"Failed to create deployment: {e}")
        return False

    return True
