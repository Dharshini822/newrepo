import os
from flask import Flask, send_from_directory, jsonify
import config
from backend.services.db_service import init_db
from backend.routes.status_routes import status_bp
from backend.routes.predict_routes import predict_bp
from backend.routes.dataset_routes import dataset_bp
from backend.routes.train_routes import train_bp
from backend.routes.translate_routes import translate_bp
from backend.routes.history_routes import history_bp

def create_app():
    app = Flask(__name__, static_folder=config.FRONTEND_DIR)
    app.config["MAX_CONTENT_LENGTH"] = config.MAX_CONTENT_LENGTH

    # Initialize SQLite database
    init_db()

    # Register API blueprints
    app.register_blueprint(status_bp, url_prefix="/api")
    app.register_blueprint(predict_bp, url_prefix="/api")
    app.register_blueprint(dataset_bp, url_prefix="/api")
    app.register_blueprint(train_bp, url_prefix="/api")
    app.register_blueprint(translate_bp, url_prefix="/api")
    app.register_blueprint(history_bp, url_prefix="/api")

    # Add CORS headers
    @app.after_request
    def add_cors_headers(response):
        response.headers["Access-Control-Allow-Origin"] = "*"
        response.headers["Access-Control-Allow-Headers"] = "Content-Type,Authorization"
        response.headers["Access-Control-Allow-Methods"] = "GET,POST,PUT,DELETE,OPTIONS"
        return response

    # Serve Frontend Single Page App
    @app.route("/")
    def index():
        return send_from_directory(config.FRONTEND_DIR, "index.html")

    @app.route("/<path:path>")
    def static_files(path):
        target_path = os.path.join(config.FRONTEND_DIR, path)
        if os.path.exists(target_path):
            return send_from_directory(config.FRONTEND_DIR, path)
        return send_from_directory(config.FRONTEND_DIR, "index.html")

    # Error handlers
    @app.errorhandler(413)
    def request_entity_too_large(error):
        return jsonify({
            "success": False,
            "error": "Uploaded file is too large. Maximum supported archive size is 100MB."
        }), 413

    @app.errorhandler(404)
    def not_found(error):
        return jsonify({
            "success": False,
            "error": "The requested API endpoint was not found."
        }), 404

    @app.errorhandler(500)
    def internal_error(error):
        return jsonify({
            "success": False,
            "error": "Internal server error occurred."
        }), 500

    return app

# Create Flask application instance for Vercel
app = create_app()

if __name__ == "__main__":
    print("===============================================================")
    print("  SignAI — AI-Powered Multilingual Sign Language System")
    print("  Server running at: http://127.0.0.1:5000")
    print("===============================================================")

    app.run(host="0.0.0.0", port=5000, debug=False)