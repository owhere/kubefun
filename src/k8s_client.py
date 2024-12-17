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
    
storage_api = client.StorageV1Api()
rbac_api = client.RbacAuthorizationV1Api()
api_ext = client.ApiextensionsV1Api()

def get_nodes():
    """Retrieve nodes from Kubernetes."""
    nodes = core_api.list_node()
    return [{"name": n.metadata.name, "status": n.status.conditions[-1].type} for n in nodes.items]

def get_pods():
    """Retrieve pods from Kubernetes."""
    pods = core_api.list_pod_for_all_namespaces()
    return [{"name": p.metadata.name, "namespace": p.metadata.namespace, "status": p.status.phase} for p in pods.items]

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

def get_storage_classes():
    """Retrieve Storage Classes from Kubernetes."""
    try:
        config.load_kube_config()
    except Exception:
        config.load_incluster_config()

    storage_classes = storage_api.list_storage_class()
    return [{"name": sc.metadata.name, "provisioner": sc.provisioner} for sc in storage_classes.items]

def get_persistent_volumes():
    """Retrieve Persistent Volumes (PVs) from Kubernetes."""
    try:
        config.load_kube_config()
    except Exception:
        config.load_incluster_config()

    core_api = client.CoreV1Api()
    pvs = core_api.list_persistent_volume()
    return [{"name": pv.metadata.name, "capacity": pv.spec.capacity['storage'], "status": pv.status.phase} for pv in pvs.items]

def get_persistent_volume_claims():
    """Retrieve Persistent Volume Claims (PVCs) from Kubernetes."""
    try:
        config.load_kube_config()
    except Exception:
        config.load_incluster_config()

    core_api = client.CoreV1Api()
    pvcs = core_api.list_persistent_volume_claim_for_all_namespaces()
    return [{"name": pvc.metadata.name, "namespace": pvc.metadata.namespace, "status": pvc.status.phase} for pvc in pvcs.items]

def get_namespaces_with_counts():
    """
    Retrieve namespaces with counts for pods, deployments, and services.
    """
    try:
        config.load_kube_config()
    except Exception:
        config.load_incluster_config()

    core_api = client.CoreV1Api()
    apps_api = client.AppsV1Api()

    # Get namespaces
    namespaces = core_api.list_namespace()

    # Initialize counts per namespace
    namespace_data = []

    # Fetch all pods, deployments, and services
    pods = core_api.list_pod_for_all_namespaces().items
    deployments = apps_api.list_deployment_for_all_namespaces().items
    services = core_api.list_service_for_all_namespaces().items

    # Aggregate counts
    for ns in namespaces.items:
        ns_name = ns.metadata.name

        pod_count = len([p for p in pods if p.metadata.namespace == ns_name])
        deployment_count = len([d for d in deployments if d.metadata.namespace == ns_name])
        service_count = len([s for s in services if s.metadata.namespace == ns_name])

        namespace_data.append({
            "name": ns_name,
            "status": "Active" if not ns.status.phase else ns.status.phase,
            "pods": pod_count,
            "deployments": deployment_count,
            "services": service_count
        })

    return namespace_data

def search_kubernetes_resources(query):
    """
    Search Kubernetes resources (namespace-scoped and cluster-level) that match the given keyword.
    """
    try:
        config.load_kube_config()
    except Exception:
        config.load_incluster_config()

    core_api = client.CoreV1Api()
    apps_api = client.AppsV1Api()
    batch_api = client.BatchV1Api()
    networking_api = client.NetworkingV1Api()
    storage_api = client.StorageV1Api()
    rbac_api = client.RbacAuthorizationV1Api()
    admission_api = client.AdmissionregistrationV1Api()
    api_registration_api = client.ApiregistrationV1Api()
    api_ext = client.ApiextensionsV1Api()

    results = []

    # Cluster-Level Resources
    # Nodes
    nodes = core_api.list_node()
    for node in nodes.items:
        if query.lower() in node.metadata.name.lower():
            results.append({
                "type": "Node",
                "name": node.metadata.name,
                "namespace": "N/A",
                "status": "Ready" if any(cond.type == "Ready" and cond.status == "True" for cond in node.status.conditions) else "NotReady"
            })

    # Persistent Volumes
    pvs = core_api.list_persistent_volume()
    for pv in pvs.items:
        if query.lower() in pv.metadata.name.lower():
            results.append({
                "type": "Persistent Volume",
                "name": pv.metadata.name,
                "namespace": "N/A",
                "status": pv.status.phase
            })

    # Storage Classes
    storage_classes = storage_api.list_storage_class()
    for sc in storage_classes.items:
        if query.lower() in sc.metadata.name.lower():
            results.append({
                "type": "Storage Class",
                "name": sc.metadata.name,
                "namespace": "N/A",
                "status": sc.provisioner
            })

    # ClusterRoles
    cluster_roles = rbac_api.list_cluster_role()
    for cr in cluster_roles.items:
        if query.lower() in cr.metadata.name.lower():
            results.append({
                "type": "ClusterRole",
                "name": cr.metadata.name,
                "namespace": "N/A",
                "status": "Defined"
            })

    # ClusterRoleBindings
    cluster_role_bindings = rbac_api.list_cluster_role_binding()
    for crb in cluster_role_bindings.items:
        if query.lower() in crb.metadata.name.lower():
            results.append({
                "type": "ClusterRoleBinding",
                "name": crb.metadata.name,
                "namespace": "N/A",
                "status": "Bound"
            })

    # CRDs
    crds = api_ext.list_custom_resource_definition()
    for crd in crds.items:
        if query.lower() in crd.metadata.name.lower():
            results.append({
                "type": "Custom Resource Definition",
                "name": crd.metadata.name,
                "namespace": "N/A",
                "status": "Defined"
            })

    # MutatingWebhookConfigurations
    mwcs = admission_api.list_mutating_webhook_configuration()
    for mwc in mwcs.items:
        if query.lower() in mwc.metadata.name.lower():
            results.append({
                "type": "MutatingWebhookConfiguration",
                "name": mwc.metadata.name,
                "namespace": "N/A",
                "status": "Configured"
            })

    # ValidatingWebhookConfigurations
    vwcs = admission_api.list_validating_webhook_configuration()
    for vwc in vwcs.items:
        if query.lower() in vwc.metadata.name.lower():
            results.append({
                "type": "ValidatingWebhookConfiguration",
                "name": vwc.metadata.name,
                "namespace": "N/A",
                "status": "Configured"
            })

    # Namespace-Scoped Resources
    # Namespaces
    namespaces = core_api.list_namespace()
    for ns in namespaces.items:
        if query.lower() in ns.metadata.name.lower():
            results.append({
                "type": "Namespace",
                "name": ns.metadata.name,
                "namespace": "N/A",
                "status": "Active"
            })

    # Pods
    pods = core_api.list_pod_for_all_namespaces()
    for pod in pods.items:
        if query.lower() in pod.metadata.name.lower() or query.lower() in pod.metadata.namespace.lower():
            results.append({
                "type": "Pod",
                "name": pod.metadata.name,
                "namespace": pod.metadata.namespace,
                "status": pod.status.phase
            })

    # Persistent Volume Claims
    pvcs = core_api.list_persistent_volume_claim_for_all_namespaces()
    for pvc in pvcs.items:
        if query.lower() in pvc.metadata.name.lower():
            results.append({
                "type": "Persistent Volume Claim",
                "name": pvc.metadata.name,
                "namespace": pvc.metadata.namespace,
                "status": pvc.status.phase
            })

    # ConfigMaps
    configmaps = core_api.list_config_map_for_all_namespaces()
    for cm in configmaps.items:
        if query.lower() in cm.metadata.name.lower():
            results.append({
                "type": "ConfigMap",
                "name": cm.metadata.name,
                "namespace": cm.metadata.namespace,
                "status": "Available"
            })

    # Deployments
    deployments = apps_api.list_deployment_for_all_namespaces()
    for deployment in deployments.items:
        if query.lower() in deployment.metadata.name.lower():
            results.append({
                "type": "Deployment",
                "name": deployment.metadata.name,
                "namespace": deployment.metadata.namespace,
                "status": f"Replicas: {deployment.spec.replicas}"
            })

    # StatefulSets
    statefulsets = apps_api.list_stateful_set_for_all_namespaces()
    for ss in statefulsets.items:
        if query.lower() in ss.metadata.name.lower():
            results.append({
                "type": "StatefulSet",
                "name": ss.metadata.name,
                "namespace": ss.metadata.namespace,
                "status": f"Replicas: {ss.spec.replicas}"
            })

    # DaemonSets
    daemonsets = apps_api.list_daemon_set_for_all_namespaces()
    for ds in daemonsets.items:
        if query.lower() in ds.metadata.name.lower():
            results.append({
                "type": "DaemonSet",
                "name": ds.metadata.name,
                "namespace": ds.metadata.namespace,
                "status": f"Desired: {ds.status.desired_number_scheduled}"
            })

    return results

