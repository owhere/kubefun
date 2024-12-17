from kubernetes import client, config
import os

# Load Kubernetes configuration
try:
    config.load_kube_config()  # Local kubeconfig
except Exception:
    config.load_incluster_config()  # In-cluster config

# Initialize Kubernetes API clients
core_api = client.CoreV1Api()
apps_api = client.AppsV1Api()

def get_nodes():
    """Retrieve nodes from Kubernetes."""
    nodes = core_api.list_node()
    return [{"name": n.metadata.name, "status": n.status.conditions[-1].type} for n in nodes.items]

def get_pods():
    """Retrieve pods from Kubernetes."""
    pods = core_api.list_pod_for_all_namespaces()
    return [{"name": p.metadata.name, "namespace": p.metadata.namespace, "status": p.status.phase} for p in pods.items]

def search_kubernetes_resources(query):
    """
    Search Kubernetes resources (pods, nodes, deployments) that match the given keyword.
    """
    results = []

     # Search Namespaces
    namespaces = core_api.list_namespace()
    for ns in namespaces.items:
        if query.lower() in ns.metadata.name.lower():
            results.append({
                "type": "Namespace",
                "name": ns.metadata.name,
                "namespace": "N/A",
                "status": "Active"
            })

    # Search Pods
    pods = core_api.list_pod_for_all_namespaces()
    for pod in pods.items:
        if query.lower() in pod.metadata.name.lower():
            results.append({
                "type": "Pod",
                "name": pod.metadata.name,
                "namespace": pod.metadata.namespace,
                "status": pod.status.phase
            })

    # Search Nodes
    nodes = core_api.list_node()
    for node in nodes.items:
        if query.lower() in node.metadata.name.lower():
            results.append({
                "type": "Node",
                "name": node.metadata.name,
                "namespace": "N/A",
                "status": node.status.conditions[-1].type
            })

    # Search Deployments
    deployments = apps_api.list_deployment_for_all_namespaces()
    for deployment in deployments.items:
        if query.lower() in deployment.metadata.name.lower():
            results.append({
                "type": "Deployment",
                "name": deployment.metadata.name,
                "namespace": deployment.metadata.namespace,
                "status": f"Replicas: {deployment.spec.replicas}"
            })

    # Search Services
    services = core_api.list_service_for_all_namespaces()
    for svc in services.items:
        if query.lower() in svc.metadata.name.lower():
            results.append({
                "type": "Service",
                "name": svc.metadata.name,
                "namespace": svc.metadata.namespace,
                "status": svc.spec.type
            })

    return results

def get_cluster_info():
    """
    Fetch basic cluster information like API server URL, health, and resource counts.
    """
    cluster_info = {}

    # API Server URL
    current_config = client.Configuration.get_default_copy()
    cluster_info["api_server"] = current_config.host

    # Context Name (Cluster Name derived from kubeconfig)
    cluster_info["cluster_name"] = os.getenv("KUBERNETES_CLUSTER_NAME", "Unknown Cluster")

    # Check Node Health
    nodes = core_api.list_node()
    total_nodes = len(nodes.items)
    ready_nodes = sum(1 for node in nodes.items if any(
        cond.type == "Ready" and cond.status == "True" for cond in node.status.conditions
    ))

    cluster_info["total_nodes"] = total_nodes
    cluster_info["healthy_nodes"] = ready_nodes
    cluster_info["health_status"] = "Healthy" if total_nodes == ready_nodes else "Unhealthy"

    # Count Pods
    pods = core_api.list_pod_for_all_namespaces()
    cluster_info["total_pods"] = len(pods.items)

    # Count Deployments
    deployments = apps_api.list_deployment_for_all_namespaces()
    cluster_info["total_deployments"] = len(deployments.items)

    # Count Services
    services = core_api.list_service_for_all_namespaces()
    cluster_info["total_services"] = len(services.items)

    return cluster_info
