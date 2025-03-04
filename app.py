from flask import Flask
from src.routes import init_routes
from src.k8s_client import load_kube_config

import logging

logging.basicConfig(
    level=logging.INFO,  # Ensure it captures DEBUG and above logs
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.StreamHandler(),  # Log to console
    ],
)

# Create Flask app
app = Flask(__name__, template_folder="templates", static_folder="static")

load_kube_config()

# Initialize routes
init_routes(app)

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=39027)
