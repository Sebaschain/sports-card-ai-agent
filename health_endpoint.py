"""
Health Check Endpoint for Sports Card AI Agent
"""

from flask import Flask, jsonify
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.utils.database import get_db
from src.utils.config import settings


def create_health_app():
    """Create minimal Flask app for health checks"""
    app = Flask(__name__)

    @app.route("/health")
    def health():
        """Health check endpoint"""
        try:
            # Test database connection
            with get_db() as db:
                db.execute("SELECT 1")

            # Test configuration
            config_ok = bool(settings.DATABASE_URL)

            health_data = {
                "status": "healthy",
                "database": "connected",
                "configuration": "ok" if config_ok else "missing",
                "app": "running",
            }

            return jsonify(health_data), 200

        except Exception as e:
            error_data = {
                "status": "unhealthy",
                "error": str(e),
                "database": "disconnected",
                "app": "error",
            }

            return jsonify(error_data), 500

    return app


if __name__ == "__main__":
    app = create_health_app()
    app.run(host="0.0.0.0", port=8502, debug=False)
