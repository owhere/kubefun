import logging
from kubernetes import client, config
import os

logger = logging.getLogger(__name__)

# Load Kubernetes configuration
def load_kube_config():
    try:
        config.load_kube_config()
        logger.info("Loaded kube config from local file.")
    except Exception:
        config.load_incluster_config()
        logger.info("Loaded in-cluster kube config.")

# Node Functions
def get_nodes():
    """Retrieve all nodes in the cluster."""
    core_api = client.CoreV1Api()
    nodes = core_api.list_node()
    return [
        {
            "type": "Node",
            "name": node.metadata.name,
            "status": "Ready" if any(
                cond.type == "Ready" and cond.status == "True"
                for cond in node.status.conditions
            ) else "NotReady"
        }
        for node in nodes.items
    ]

def search_nodes(query):
    """Search nodes by name."""
    nodes = get_nodes()
    return [node for node in nodes if query.lower() in node["name"].lower()]

# Pod Functions
def get_pods(namespace=None):
    """Retrieve pods from Kubernetes with desired and ready replicas."""
    core_api = client.CoreV1Api()
    apps_api = client.AppsV1Api()

    # Fetch Pods
    if namespace:
        pods = core_api.list_namespaced_pod(namespace)
    else:
        pods = core_api.list_pod_for_all_namespaces()

    # Fetch higher-level controllers (ReplicaSets, Deployments, StatefulSets)
    replica_sets = apps_api.list_replica_set_for_all_namespaces()
    deployments = apps_api.list_deployment_for_all_namespaces()
    stateful_sets = apps_api.list_stateful_set_for_all_namespaces()

    # Build mappings for replicas
    desired_ready_mapping = {}

    # Add ReplicaSets
    for rs in replica_sets.items:
        desired_ready_mapping[rs.metadata.name] = {
            "desired": rs.spec.replicas or 0,
            "ready": rs.status.ready_replicas or 0
        }

    # Add Deployments
    for deploy in deployments.items:
        desired_ready_mapping[deploy.metadata.name] = {
            "desired": deploy.spec.replicas or 0,
            "ready": deploy.status.ready_replicas or 0
        }

    # Add StatefulSets
    for sts in stateful_sets.items:
        desired_ready_mapping[sts.metadata.name] = {
            "desired": sts.spec.replicas or 0,
            "ready": sts.status.ready_replicas or 0
        }

    # Match Pods to their controllers
    pod_data = []
    for pod in pods.items:
        controller_name = None
        desired_replicas = "N/A"
        ready_replicas = "N/A"

        # Identify the controller
        for owner in pod.metadata.owner_references or []:
            if owner.kind in ["ReplicaSet", "StatefulSet"]:
                controller_name = owner.name
                break

        # Lookup the controller's replica counts
        if controller_name and controller_name in desired_ready_mapping:
            desired_replicas = desired_ready_mapping[controller_name]["desired"]
            ready_replicas = desired_ready_mapping[controller_name]["ready"]

        # Add pod data
        pod_data.append({
            "type": "Pod",
            "name": pod.metadata.name,
            "namespace": pod.metadata.namespace,
            "status": pod.status.phase,
            "desired_replicas": desired_replicas,
            "ready_replicas": ready_replicas
        })

    return pod_data


def search_pods(query, namespace=None):
    """Search pods by name or namespace."""
    pods = get_pods(namespace)
    return [
        pod for pod in pods
        if query.lower() in pod["name"].lower() or query.lower() in pod["namespace"].lower()
    ]

# Namespace Functions
def get_namespaces():
    """Retrieve all namespaces in the cluster."""
    core_api = client.CoreV1Api()
    namespaces = core_api.list_namespace()
    return [
        {
            "type": "Namespace",
            "name": ns.metadata.name,
            "status": ns.status.phase
        }
        for ns in namespaces.items
    ]


def search_namespaces(query):
    """Search namespaces by name."""
    namespaces = get_namespaces()
    return [ns for ns in namespaces if query.lower() in ns["name"].lower()]


# Deployment Functions
def get_deployments(namespace=None):
    """Retrieve deployments from Kubernetes."""
    apps_api = client.AppsV1Api()
    if namespace:
        deployments = apps_api.list_namespaced_deployment(namespace)
    else:
        deployments = apps_api.list_deployment_for_all_namespaces()

    return [
        {
            "type": "Deployment",
            "name": dep.metadata.name,
            "namespace": dep.metadata.namespace,
            "replicas": dep.spec.replicas,
            "ready_replicas": dep.status.ready_replicas or 0
        }
        for dep in deployments.items
    ]


def search_deployments(query, namespace=None):
    """Search deployments by name or namespace."""
    deployments = get_deployments(namespace)
    return [
        dep for dep in deployments
        if query.lower() in dep["name"].lower() or query.lower() in dep["namespace"].lower()
    ]


# Service Functions
def get_services(namespace=None):
    """Retrieve services from Kubernetes."""
    core_api = client.CoreV1Api()
    if namespace:
        services = core_api.list_namespaced_service(namespace)
    else:
        services = core_api.list_service_for_all_namespaces()

    return [
        {
            "name": svc.metadata.name,
            "namespace": svc.metadata.namespace,
            "type": svc.spec.type if svc.spec.type else "Unknown",
            "cluster_ip": svc.spec.cluster_ip if svc.spec.cluster_ip else "None",
            "ports": [
                     f"{port.port}/{port.protocol}" for port in (svc.spec.ports or [])
                     ],
        }
        for svc in services.items
    ]

def search_services(query, namespace=None):
    """Search services by name or namespace."""
    services = get_services(namespace)
    return [
        service for service in services
        if query.lower() in service["name"].lower() or query.lower() in service["namespace"].lower()
    ]

# CRDs
def get_crds():
    """Retrieve all CustomResourceDefinitions (CRDs) from Kubernetes."""
    api_ext = client.ApiextensionsV1Api()
    try:
        crds = api_ext.list_custom_resource_definition()
        return [
            {
                "name": crd.metadata.name,
                "group": crd.spec.group,
                "version": crd.spec.versions[0].name if crd.spec.versions else "N/A",
                "scope": crd.spec.scope,
                "type": crd.spec.names.kind,
            }
            for crd in crds.items
        ]
    except Exception as e:
        logger.error(f"Error fetching CRDs: {e}")
        return []
    
def search_crds(query):
    """Search CRDs by name or other fields."""
    crds = get_crds()
    return [
        crd
        for crd in crds
        if query.lower() in crd["name"].lower()
           or query.lower() in crd["group"].lower()
           or query.lower() in crd["type"].lower()
    ]

# Cluster Roles
def get_clusterroles():
    """Retrieve all ClusterRoles in the cluster."""
    rbac_api = client.RbacAuthorizationV1Api()
    try:
        clusterroles = rbac_api.list_cluster_role()
        return [
            {
                "type": "Cluster Role",
                "name": role.metadata.name,
                "creation_timestamp": role.metadata.creation_timestamp,
                "rules_count": len(role.rules) if role.rules else 0,
            }
            for role in clusterroles.items
        ]
    except Exception as e:
        logger.error(f"Error fetching ClusterRoles: {e}")
        return []

def search_clusterroles(query):
    """Search ClusterRoles by name."""
    clusterroles = get_clusterroles()
    return [
        role
        for role in clusterroles
        if query.lower() in role["name"].lower()
    ]

# Cluster Role Bindings
def get_clusterrolebindings():
    """Retrieve all ClusterRoleBindings in the cluster."""
    rbac_api = client.RbacAuthorizationV1Api()
    try:
        clusterrolebindings = rbac_api.list_cluster_role_binding()
        return [
            {
                "type": "Cluster Role Binding",
                "name": binding.metadata.name,
                "role_ref": binding.role_ref.name,
                "subjects_count": len(binding.subjects) if binding.subjects else 0,
            }
            for binding in clusterrolebindings.items
        ]
    except Exception as e:
        logger.error(f"Error fetching ClusterRoleBindings: {e}")
        return []

def search_clusterrolebindings(query):
    """Search ClusterRoleBindings by name or referenced role."""
    clusterrolebindings = get_clusterrolebindings()
    return [
        binding
        for binding in clusterrolebindings
        if query.lower() in binding["name"].lower() or query.lower() in binding["role_ref"].lower()
    ]

# Secrets Functions
def get_secrets(namespace=None):
    """Retrieve secrets from Kubernetes."""
    core_api = client.CoreV1Api()
    if namespace:
        secrets = core_api.list_namespaced_secret(namespace)
    else:
        secrets = core_api.list_secret_for_all_namespaces()

    return [
        {
            "name": secret.metadata.name,
            "namespace": secret.metadata.namespace,
            "type": secret.type
        }
        for secret in secrets.items
    ]

def search_secrets(query, namespace=None):
    """Search secrets by name or namespace."""
    secrets = get_secrets(namespace)
    return [
        secret for secret in secrets
        if query.lower() in secret["name"].lower() or query.lower() in secret["namespace"].lower()
    ]

# Storage Class Functions
def get_storage_classes():
    """Retrieve storage classes from Kubernetes."""
    storage_api = client.StorageV1Api()
    storage_classes = storage_api.list_storage_class()

    return [
        {
            "type": "Storage Class",
            "name": sc.metadata.name,
            "provisioner": sc.provisioner
        }
        for sc in storage_classes.items
    ]


def search_storage_classes(query):
    """Search storage classes by name."""
    storage_classes = get_storage_classes()
    return [sc for sc in storage_classes if query.lower() in sc["name"].lower()]


# Persistent Volume (PV) Functions
def get_persistent_volumes():
    """Retrieve persistent volumes from Kubernetes."""
    core_api = client.CoreV1Api()
    pvs = core_api.list_persistent_volume()

    return [
        {
            "type": "PV",
            "name": pv.metadata.name,
            "capacity": pv.spec.capacity["storage"],
            "status": pv.status.phase,
            "storage_class": pv.spec.storage_class_name
        }
        for pv in pvs.items
    ]


def search_persistent_volumes(query):
    """Search persistent volumes by name."""
    pvs = get_persistent_volumes()
    return [pv for pv in pvs if query.lower() in pv["name"].lower()]


# Persistent Volume Claim (PVC) Functions
def get_persistent_volume_claims(namespace=None):
    """Retrieve persistent volume claims from Kubernetes."""
    core_api = client.CoreV1Api()
    if namespace:
        pvcs = core_api.list_namespaced_persistent_volume_claim(namespace)
    else:
        pvcs = core_api.list_persistent_volume_claim_for_all_namespaces()

    return [
        {
            "type": "PVC",
            "name": pvc.metadata.name,
            "namespace": pvc.metadata.namespace,
            "storage_class": pvc.spec.storage_class_name,
            "capacity": pvc.status.capacity.get("storage", "Unknown") if pvc.status.capacity else "Unknown",
            "status": pvc.status.phase
        }
        for pvc in pvcs.items
    ]


def search_persistent_volume_claims(query, namespace=None):
    """Search persistent volume claims by name or namespace."""
    pvcs = get_persistent_volume_claims(namespace)
    return [
        pvc for pvc in pvcs
        if query.lower() in pvc["name"].lower() or query.lower() in pvc["namespace"].lower()
    ]


# General Search
def search_kubernetes_resources(query):
    """
    Search all Kubernetes resources by name or namespace.
    """
    logger.info(f"Starting global search for query: '{query}'")
    results = []

    results.extend(search_namespaces(query))
    results.extend(search_nodes(query))
    results.extend(search_pods(query))
    results.extend(search_services(query))
    results.extend(search_secrets(query))
    results.extend(search_deployments(query))
    results.extend(search_persistent_volumes(query))
    results.extend(search_persistent_volume_claims(query))
    results.extend(search_storage_classes(query))
    results.extend(search_crds(query))
    results.extend(search_clusterroles(query))  
    results.extend(search_clusterrolebindings(query))  

    logger.info(f"Global search completed. Found {len(results)} matching resources.")
    return results

def get_namespaces_with_counts():
    """
    Retrieve namespaces with counts for pods, deployments, and services.
    """

    # Get namespaces
    namespaces = get_namespaces()

    # Initialize counts per namespace
    namespace_data = []

    # Fetch all pods, deployments, and services
    pods = get_pods()
    deployments = get_deployments()
    services = get_services()
    secrets = get_secrets()

    # Aggregate counts
    for ns in namespaces:
        ns_name = ns["name"]

        # Count resources by namespace
        pod_count = len([p for p in pods if p["namespace"] == ns_name])
        deployment_count = len([d for d in deployments if d["namespace"] == ns_name])
        service_count = len([s for s in services if s["namespace"] == ns_name])
        secrets_count = len([s for s in secrets if s["namespace"] == ns_name])

        namespace_data.append({
            "name": ns_name,
            "status": "Active" if not ns["status"] else ns["status"],
            "pods": pod_count,
            "deployments": deployment_count,
            "services": service_count,
            "secrets": secrets_count
        })

    return namespace_data

def get_cluster_info():
    """
    Fetch basic cluster information like API server URL, health, and resource counts.
    """
    cluster_info = {}

    # API Server URL
    try:
        current_config = client.Configuration.get_default_copy()
        cluster_info["api_server"] = current_config.host
    except Exception as e:
        logger.error(f"Error fetching API server URL: {e}")
        cluster_info["api_server"] = "Unknown"

    # Context Name (Cluster Name)
    cluster_info["cluster_name"] = os.getenv("KUBERNETES_CLUSTER_NAME", "Unknown Cluster")

    # Check Node Health
    try:
        nodes = get_nodes()
        total_nodes = len(nodes)
        ready_nodes = sum(1 for node in nodes if node["status"] == "Ready")
        cluster_info["total_nodes"] = total_nodes
        cluster_info["healthy_nodes"] = ready_nodes
        cluster_info["health_status"] = "Healthy" if total_nodes == ready_nodes else "Unhealthy"
    except Exception as e:
        logger.error(f"Error fetching nodes: {e}")
        cluster_info["total_nodes"] = 0
        cluster_info["healthy_nodes"] = 0
        cluster_info["health_status"] = "Unknown"

    # Count Pods
    try:
        pods = get_pods()
        cluster_info["total_pods"] = len(pods)
    except Exception as e:
        logger.error(f"Error fetching pods: {e}")
        cluster_info["total_pods"] = 0

    # Count Namespaces
    try:
        namespaces = get_namespaces()
        cluster_info["total_namespaces"] = len(namespaces)
    except Exception as e:
        logger.error(f"Error fetching namespaces: {e}")
        cluster_info["total_namespaces"] = 0

    # Count Deployments
    try:
        deployments = get_deployments()
        cluster_info["total_deployments"] = len(deployments)
    except Exception as e:
        logger.error(f"Error fetching deployments: {e}")
        cluster_info["total_deployments"] = 0

    # Count Services
    try:
        services = get_services()
        cluster_info["total_services"] = len(services)
    except Exception as e:
        logger.error(f"Error fetching services: {e}")
        cluster_info["total_services"] = 0

    return cluster_info

def get_node_details(node_name):
    """
    Retrieve detailed information about a specific node.
    """
    core_api = client.CoreV1Api()
    node = core_api.read_node(name=node_name)
    return node.to_dict()  # Convert the object to a dictionary for easier display

def get_namespace_details(namespace_name):
    """
    Retrieve detailed information about a specific namespace.
    """
    core_api = client.CoreV1Api()
    namespace = core_api.read_namespace(name=namespace_name)
    return namespace.to_dict()  # Convert the object to a dictionary for easier display