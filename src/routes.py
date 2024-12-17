from flask import render_template, request
from .k8s_client import get_nodes, get_pods, search_kubernetes_resources, get_cluster_info

def init_routes(app):
    """Register all routes for the Flask app."""

    @app.route('/')
    def welcome():
        cluster_info = get_cluster_info()
        return render_template("welcome.html", cluster_info=cluster_info)
    
    @app.route('/kube')
    def kube():
        nodes = get_nodes()
        return render_template("kube.html", nodes=nodes)

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

    @app.route('/volume')
    def volume():
        return render_template("volume.html")

    @app.route('/apps')
    def apps():
        return render_template("apps.html")

    @app.route('/about')
    def about():
        return render_template("about.html")