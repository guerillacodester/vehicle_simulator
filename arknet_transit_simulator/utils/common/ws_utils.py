# ws_utils.py
from urllib.parse import urlparse, urlunparse, parse_qsl, urlencode

def to_ws_url(base: str, token: str, device_id: str) -> str:
    """
    Normalise a WebSocket base URL for the GPS server.

    Parameters
    ----------
    base: str
        The base URL, e.g. 'ws://localhost:5000' or 'wss://example.com/api'.
        Must begin with ws:// or wss:// (bare host:port is accepted and assumed
        to be ws://).  HTTP/HTTPS URLs are rejected.

    token: str
        Authentication token expected by the server.

    device_id: str
        The unique device identifier.

    Returns
    -------
    str
        A URL ending in '/device' with the given token and deviceId as
        query parameters.  Existing query parameters are preserved.
    """
    s = (base or "").strip()
    if not s:
        s = "ws://localhost:5000"

    # Only ws:// and wss:// schemes are allowed.
    if not s.startswith(("ws://", "wss://")):
        if "://" in s:
            raise ValueError("WebSocket URL must start with ws:// or wss://")
        s = "ws://" + s.lstrip("/")

    u = urlparse(s)
    scheme, netloc = u.scheme, u.netloc
    path = (u.path or "").rstrip("/")

    # Ensure the path ends with '/device'.
    if not path or not path.endswith("/device"):
        path = (path + "/device") if path else "/device"

    # Merge existing query params with token/deviceId.
    qd = dict(parse_qsl(u.query, keep_blank_values=True))
    if token and "token" not in qd:
        qd["token"] = token
    if device_id and "deviceId" not in qd:
        qd["deviceId"] = device_id

    return urlunparse((scheme, netloc, path, "", urlencode(qd), ""))
