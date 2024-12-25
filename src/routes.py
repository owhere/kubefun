from flask import render_template, request
from .k8s_client import search_nodes, search_pods, search_secrets, search_services
from .k8s_client import get_nodes, get_pods, get_secrets, get_services

from .k8s_client import get_namespaces_with_counts, search_kubernetes_resources, get_cluster_info
from .k8s_client import get_storage_classes, get_persistent_volumes, get_persistent_volume_claims
from .k8s_client import get_node_details, get_namespace_details

def init_routes(app):
    """Register all routes for the Flask app."""

    @app.route('/')
    def welcome():
        cluster_info = get_cluster_info()
        return render_template("welcome.html", cluster_info=cluster_info)
    
    @app.route('/kube')
    def kube():
        nodes = get_nodes()
        namespaces = get_namespaces_with_counts()
        return render_template('kube.html', nodes=nodes, namespaces=namespaces)

    @app.route('/pods')
    def pods():
        pods = get_pods()
        return render_template("pods.html", pods=pods)

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
        storage_classes = get_storage_classes()
        persistent_volumes = get_persistent_volumes()
        persistent_volume_claims = get_persistent_volume_claims()

        return render_template('volumes.html', 
                            storage_classes=storage_classes, 
                            persistent_volumes=persistent_volumes, 
                            persistent_volume_claims=persistent_volume_claims)

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


    @app.route('/apps')
    def apps():
        """Render the Services page."""
        services_list = get_services()
        return render_template("apps.html", services=services_list)

    @app.route('/about')
    def about():
        return render_template("about.html")