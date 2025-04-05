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
