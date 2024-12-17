from flask import Flask
from src.routes import init_routes

# Create Flask app
app = Flask(__name__, template_folder="templates", static_folder="static")

# Initialize routes
init_routes(app)

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=39027)
