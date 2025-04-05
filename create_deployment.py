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


def getDeploymentDetails(release_name, namespace):
    try:
        deployment_name = f"{release_name}-deployment"
        service_name = f"{release_name}-service"
        scaledobject_name = f"{release_name}-scaledobject"

        # Deployment
        deployment_json = runKubectlCommand([
            "get", "deployment", deployment_name,
            "-n", namespace,
            "-o", "json"
        ])
        deployment = json.loads(deployment_json)
        replicas = deployment['spec']['replicas']
        available = deployment['status'].get('availableReplicas', 0)

        # Service
        service_json = runKubectlCommand([
            "get", "svc", service_name,
            "-n", namespace,
            "-o", "json"
        ])
        service = json.loads(service_json)
        node_port = service['spec']['ports'][0].get('nodePort')
        service_port = service['spec']['ports'][0].get('port')
        endpoint = f"http://localhost:{node_port}" if node_port else "N/A"

        # Scaling (KEDA ScaledObject)
        try:
            scaledobject_json = runKubectlCommand([
                "get", "scaledobject", scaledobject_name,
                "-n", namespace,
                "-o", "json"
            ])
            scaledobject = json.loads(scaledobject_json)
            min_replicas = scaledobject['spec'].get('minReplicaCount')
            max_replicas = scaledobject['spec'].get('maxReplicaCount')
            triggers = scaledobject['spec'].get('triggers', [])
        except subprocess.CalledProcessError:
            min_replicas = max_replicas = "N/A"
            triggers = []

        return {
            "deployment": {
                "name": deployment_name,
                "replicas": replicas,
                "available": available
            },
            "service": {
                "name": service_name,
                "port": service_port,
                "nodePort": node_port,
                "endpoint": endpoint
            },
            "scaling": {
                "minReplicas": min_replicas,
                "maxReplicas": max_replicas,
                "triggers": triggers
            }
        }

    except Exception as e:
        print(f"⚠️ Failed to fetch deployment details: {e}")
        return {}
