from flask import render_template, request
from .k8s_client import get_nodes, get_pods, get_secrets, get_services, get_deployments, get_statefulsets
from .k8s_client import get_namespaces_with_counts, search_kubernetes_resources, get_cluster_info
from .k8s_client import get_storage_classes, get_persistent_volumes, get_persistent_volume_claims
from .k8s_client import get_node_details, get_namespace_details, get_deployment_details, get_pod_details, get_pod_events, get_statefulset_details
from .k8s_client import get_service_details, get_secret_details, get_storageclass_details
from .k8s_client import get_top_nodes, get_top_pods, get_pv_details, get_pvc_details

def init_routes(app):
    """Register all routes for the Flask app."""

    @app.route('/')
    def welcome():
        cluster_info = get_cluster_info()
        return render_template("welcome.html", cluster_info=cluster_info)
    
    @app.route('/dashboard')
    def dashboard():
        cluster_info = get_cluster_info()

        return render_template("dashboard.html", cluster_info=cluster_info)
    
    @app.route('/nodes')
    def nodes():
        nodes = get_nodes()
        top_nodes = get_top_nodes()
        # Handle errors if metrics fetch fails
        if isinstance(top_nodes, dict) and "error" in top_nodes:
            return f"Error fetching node metrics: {top_nodes['error']}", 500
        return render_template('nodes.html', nodes=nodes, top_nodes=top_nodes)
    
    @app.route('/namespaces')
    def namespaces():
        namespaces = get_namespaces_with_counts()
        return render_template('namespaces.html', namespaces=namespaces)

    @app.route('/deployments')
    def deployments():
        """Display deployments, optionally filtered by namespace."""
        namespace = request.args.get('namespace')  
        deployments = get_deployments(namespace)
        statefulsets = get_statefulsets(namespace)

        return render_template('deployments.html', deployments=deployments, statefulsets=statefulsets, namespace=namespace)

    @app.route('/pods')
    def pods():
        """Display Pods, optionally filtered by namespace."""
        namespace = request.args.get('namespace')  
        pods = get_pods(namespace)  
        top_pods = get_top_pods()
        if isinstance(top_pods, dict) and "error" in top_pods:
            return f"Error fetching pod metrics: {top_pods['error']}", 500
        return render_template("pods.html", pods=pods, namespace=namespace, top_pods=top_pods)

    @app.route('/search')
    def search():
        query = request.args.get('query', '').strip()
        results = []

        if query:
            results = search_kubernetes_resources(query)

        cluster_info = get_cluster_info()
        return render_template("welcome.html", results=results, query=query, cluster_info=cluster_info)

    @app.route('/volumes')
    def volumes():
        """Render the volumes page with updated data."""
        # Fetch the data
        storage_classes = get_storage_classes()
        persistent_volumes = get_persistent_volumes()
        persistent_volume_claims = get_persistent_volume_claims()

        # Prepare data for relationships (if required)
        pv_pvc_relationships = []
        for pvc in persistent_volume_claims:
            matched_pv = next(
                (pv for pv in persistent_volumes if pv["name"] == pvc["volume_name"]),
                None
            )
            pv_pvc_relationships.append({
                "PVC": pvc,
                "PV": matched_pv
            })

        return render_template(
            'volumes.html',
            storage_classes=storage_classes,
            persistent_volumes=persistent_volumes,
            persistent_volume_claims=persistent_volume_claims,
            pv_pvc_relationships=pv_pvc_relationships
        )


    @app.route('/node/<node_name>')
    def node_detail(node_name):
        """Route to display details of a specific node."""
        node_details = get_node_details(node_name)
        return render_template('details.html', resource_name=node_name, resource_type="Node", details=node_details)

    @app.route('/namespace/<namespace_name>')
    def namespace_detail(namespace_name):
        """Route to display details of a specific namespace."""
        namespace_details = get_namespace_details(namespace_name)
        return render_template('details.html', resource_name=namespace_name, resource_type="Namespace", details=namespace_details)

    @app.route("/deployment/<namespace>/<deployment_name>")
    def deployment_details(namespace, deployment_name):
        """Render deployment details."""
        details = get_deployment_details(namespace, deployment_name)
        if "error" in details:
            return details["error"], 400
        return render_template("deployment_details.html", deployment=details)
    
    @app.route('/statefulset/<namespace>/<name>')
    def statefulset_details(namespace, name):
        details = get_statefulset_details(namespace, name)
        return render_template('statefulset_details.html', statefulset=details)
    
    @app.route("/statefulsets/<namespace>/<stateful_name>")
    def stateful_details(namespace, stateful_name):
        """Render deployment details."""
        details = get_statefulset_details(namespace, stateful_name)
        if "error" in details:
            return details["error"], 400
        return render_template("deployment_details.html", deployment=details)

    @app.route("/pod/<namespace>/<pod_name>")
    def pod_details(namespace, pod_name):
        """Render pod details."""
        details = get_pod_details(namespace, pod_name)
        events = get_pod_events(namespace, pod_name)
        if "error" in details:
            return details["error"], 400
        return render_template("pod_details.html", pod=details, events=events)

    @app.route('/services')
    def services():
        """Display Services, optionally filtered by namespace."""
        namespace = request.args.get('namespace')  
        services_list = get_services(namespace)
        return render_template("services.html", services=services_list, namespace=namespace)

    @app.route('/secrets')
    def secrets():
        """Display Secrets, optionally filtered by namespace."""
        namespace = request.args.get('namespace')  
        secrets_list = get_secrets(namespace)
        return render_template("secrets.html", secrets=secrets_list, namespace=namespace)
    
    @app.route("/service/<namespace>/<service_name>")
    def service_details(namespace, service_name):
        """Render service details."""
        details = get_service_details(namespace, service_name)
        if "error" in details:
            return details["error"], 400
        return render_template("service_details.html", service=details)
    
    @app.route("/secret/<namespace>/<secret_name>")
    def secret_details(namespace, secret_name):
        """Render secret details."""
        details = get_secret_details(namespace, secret_name)
        if "error" in details:
            return details["error"], 400
        return render_template("secret_details.html", secret=details)
    
    @app.route("/storageclass/<storageclass_name>")
    def storageclass_details(storageclass_name):
        """Render storageclass details."""
        details = get_storageclass_details(storageclass_name)
        if "error" in details:
            return details["error"], 400
        return render_template("storageclass_details.html", storageclass=details)

    @app.route('/pv/<name>')
    def pv_details(name):
        """Display details of a specific Persistent Volume."""
        details = get_pv_details(name)
        return render_template(
            'details.html',
            resource_type="Persistent Volume",
            resource_name=name,
            details=details
        )
    
    @app.route('/pvc/<namespace>/<name>')
    def pvc_details(namespace, name):
        """Display details of a specific Persistent Volume Claim."""
        details = get_pvc_details(namespace, name)
        return render_template(
            'details.html',
            resource_type="Persistent Volume Claim",
            resource_name=f"{namespace}/{name}",
            details=details
        )

    @app.route('/about')
    def about():
        return render_template("about.html")
    