"""Launch the Flask application with the SQLite history routes enabled."""

from app import app
from history_routes import register_history_routes


register_history_routes(app)


if __name__ == "__main__":
    app.run(debug=True, host="127.0.0.1", port=5000)
