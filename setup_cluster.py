import subprocess

from kubernetes import client, config


def connectToKubernetesCluster(configFilePath):
    """
    Connect to a Kubernetes cluster using the provided configuration file path.

    Args:
        configFilePath (str): Path to the Kubernetes configuration file.

    Returns:
        bool: True if connection is successful, False otherwise.
    """
    try:
        config.load_kube_config(config_file=configFilePath)
        print("Connected to Kubernetes cluster successfully.")
        return True
    except Exception as e:
        print(f"Failed to connect to Kubernetes cluster: {e}")
        return False


def installHelm():
    """
    install helm
    """

    try:
        subprocess.run(["curl", "-fsSL", "-o", "get_helm.sh",
                        "https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3"], check=True)
        subprocess.run(["chmod", "700", "get_helm.sh"], check=True)
        subprocess.run(["./get_helm.sh"], check=True)
        print("Helm installed successfully.")
    except subprocess.CalledProcessError as e:
        print(f"Failed to install Helm: {e}")
        return False


def installKEDA():
    """
    Install KEDA using Helm.
    """
    try:
        subprocess.run(["helm", "repo", "add", "kedacore", "https://kedacore.github.io/charts"], check=True)
        subprocess.run(["helm", "repo", "update"], check=True)
        subprocess.run(["helm", "install", "keda", "kedacore/keda"], check=True)
        print("KEDA installed successfully.")
    except subprocess.CalledProcessError as e:
        print(f"Failed to install KEDA: {e}")
        return False


def summarizeClusterSetup():
    try:
        contexts, current_context = config.list_kube_config_contexts()
        print("Available contexts:")
        for context in contexts:
            print(f"- {context['name']}")
        print(f"Current context: {current_context}")

        v1 = client.CoreV1Api()
        nodes = v1.list_node()
        print("Cluster nodes:")
        for node in nodes.items:
            print(f"- {node.metadata.name}")
    except Exception as e:
        print(f"Failed to summarize cluster setup: {e}")
