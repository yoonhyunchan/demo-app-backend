from app import app as flask_app

try:
	from asgiref.wsgi import WsgiToAsgi
except ImportError as exc:
	raise RuntimeError("asgiref is required to run Flask via uvicorn. Please install asgiref.") from exc

# Expose ASGI application for uvicorn
application = WsgiToAsgi(flask_app)
