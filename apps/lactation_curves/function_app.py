"""Azure Functions entry point wrapping the FastAPI app via ASGI middleware.

Azure Functions uses this file as its entry point (looks for `app` in `function_app.py`).
The AsgiFunctionApp adapter translates between Azure Functions' HTTP handling and
FastAPI's ASGI protocol, so all existing FastAPI routes work without modification.

Request flow:
  HTTP request -> Azure Functions host -> AsgiFunctionApp -> FastAPI app -> response

Auth level is set to ANONYMOUS (no function key required). Change to FUNCTION
or ADMIN if you want to require an API key in the URL (?code=<key>).
"""

import azure.functions as func

from main import app as fastapi_app

# The variable MUST be named `app` - Azure Functions host looks for this by default
app = func.AsgiFunctionApp(app=fastapi_app, http_auth_level=func.AuthLevel.ANONYMOUS)
