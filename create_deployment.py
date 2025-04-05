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
        # Get Deployment details
        deployment_json = runKubectlCommand([
            "get", "deployment", f"{release_name}-deployment",
            "-n", namespace, "-o", "json"
        ])
        deployment = json.loads(deployment_json)

        replicas = deployment['spec']['replicas']
        image = deployment['spec']['template']['spec']['containers'][0]['image']
        container_port = deployment['spec']['template']['spec']['containers'][0]['ports'][0]['containerPort']

        print(f"\n✅ Deployment '{release_name}-deployment':")
        print(f"  🔹 Image: {image}")
        print(f"  🔹 Replicas: {replicas}")
        print(f"  🔹 Container Port: {container_port}")

        # Get Service details
        service_json = runKubectlCommand([
            "get", "service", f"{release_name}-service",
            "-n", namespace, "-o", "json"
        ])
        service = json.loads(service_json)

        cluster_ip = service['spec'].get('clusterIP', 'N/A')
        node_port = service['spec']['ports'][0].get('nodePort', 'N/A')
        service_port = service['spec']['ports'][0]['port']

        cluster_dns = f"{release_name}-service.{namespace}.svc.cluster.local"

        print(f"\n🌐 Service '{release_name}-service':")
        print(f"  🔹 ClusterIP: {cluster_ip}")
        print(f"  🔹 Port: {service_port}")
        if node_port != 'N/A':
            print(f"  🔹 NodePort: {node_port}")
        print(f"  🔹 Cluster DNS: {cluster_dns}")

        # Get KEDA ScaledObject (optional if enabled)
        try:
            scaled_object_json = runKubectlCommand([
                "get", "scaledobject.keda.sh", f"{release_name}-scaledobject",
                "-n", namespace, "-o", "json"
            ])
            scaled_object = json.loads(scaled_object_json)
            min_replicas = scaled_object['spec'].get('minReplicaCount', 'N/A')
            max_replicas = scaled_object['spec'].get('maxReplicaCount', 'N/A')
            triggers = scaled_object['spec'].get('triggers', [])

            print(f"\n📈 KEDA ScaledObject '{release_name}-scaledobject':")
            print(f"  🔹 Min Replicas: {min_replicas}")
            print(f"  🔹 Max Replicas: {max_replicas}")
            print("  🔹 Triggers:")
            for trigger in triggers:
                print(f"    - {trigger['type']}: {trigger.get('metadata', {})}")

        except subprocess.CalledProcessError:
            print("\nℹ️ KEDA ScaledObject not found or not enabled.")

    except subprocess.CalledProcessError as e:
        print(f"❌ Error fetching deployment info: {e}")
