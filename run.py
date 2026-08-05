from flask_socketio import emit
from app import create_app
from app.extensions import socketio
from app.services.stock_service import get_live_data

app = create_app()

@socketio.on("subscribe_symbol")
def subscribe_symbol(payload):
    symbol = (payload or {}).get("symbol", "AAPL")
    try:
        data = get_live_data(symbol)
        emit("live_update", {"ok": True, "data": data})
    except Exception as exc:
        emit("live_update", {"ok": False, "error": str(exc)})

@socketio.on("poll_symbol")
def poll_symbol(payload):
    symbol = (payload or {}).get("symbol", "AAPL")
    try:
        data = get_live_data(symbol)
        emit("live_update", {"ok": True, "data": data})
    except Exception as exc:
        emit("live_update", {"ok": False, "error": str(exc)})

@socketio.on("connect")
def handle_connect():
    print("Client connected")

@socketio.on("disconnect")
def handle_disconnect():
    print("Client disconnected")

if __name__ == "__main__":
    socketio.run(app, host="0.0.0.0", port=5000, debug=True, allow_unsafe_werkzeug=True)