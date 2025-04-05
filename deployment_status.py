import json
import subprocess

from utils import runKubectlCommand


def getDeploymentHealthStatus(release_name, namespace):
    print(f"\n🔍 Checking health status for deployment '{release_name}' in namespace '{namespace}'...")

    # 1. Check deployment status
    try:
        deployment = json.loads(runKubectlCommand([
            "get", "deployment", f"{release_name}-deployment",
            "-n", namespace, "-o", "json"
        ]))

        desired = deployment['status']['replicas']
        available = deployment['status'].get('availableReplicas', 0)
        ready = deployment['status'].get('readyReplicas', 0)

        print(f"\n📦 Deployment Status:")
        print(f"  🔹 Desired Replicas: {desired}")
        print(f"  🔹 Ready Replicas: {ready}")
        print(f"  🔹 Available Replicas: {available}")

        if ready == desired:
            print("  ✅ Deployment is healthy.")
        else:
            print("  ⚠️ Deployment is not fully ready.")

    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to retrieve deployment: {e}")
        return

    # 2. Check pod status
    try:
        pods_json = runKubectlCommand([
            "get", "pods", "-l", f"app={release_name}",
            "-n", namespace, "-o", "json"
        ])
        pods = json.loads(pods_json).get("items", [])

        print(f"\n🧩 Pod Status:")
        for pod in pods:
            pod_name = pod["metadata"]["name"]
            phase = pod["status"]["phase"]
            ready_conditions = [c for c in pod["status"].get("conditions", []) if c["type"] == "Ready"]
            is_ready = ready_conditions[0]["status"] if ready_conditions else "Unknown"

            print(f"  - {pod_name}: Status = {phase}, Ready = {is_ready}")

    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to retrieve pods: {e}")

    # 3. Get CPU and memory usage
    try:
        top_output = runKubectlCommand([
            "top", "pods", "-l", f"app={release_name}", "-n", namespace
        ])
        print(f"\n📊 Resource Usage (CPU/Memory):")
        print(top_output)

    except subprocess.CalledProcessError:
        print("⚠️ Metrics not available. Make sure Metrics Server is installed.")

    # 4. Get events (errors/warnings)
    try:
        events_output = runKubectlCommand([
            "get", "events", "-n", namespace, "--field-selector",
            f"involvedObject.kind=Deployment,involvedObject.name={release_name}-deployment"
        ])
        print(f"\n📣 Events:")
        print(events_output)

    except subprocess.CalledProcessError:
        print("⚠️ Unable to fetch events.")


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
