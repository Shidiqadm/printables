"""Send shapes to the standalone OCP viewer (http://localhost:3939) if it is running.

Start the viewer with:  uv run python -m ocp_viewer --port 3939
"""

import socket


def _viewer_up(port: int = 3939) -> bool:
    try:
        with socket.create_connection(("127.0.0.1", port), timeout=0.3):
            return True
    except OSError:
        return False


def preview(*objs, names=None, port: int = 3939, **kwargs) -> None:
    """Show objects in the live viewer; silently skip if the viewer is not running."""
    if not _viewer_up(port):
        print(f"[preview] viewer not running on :{port} (uv run python -m ocp_viewer) - skipped")
        return
    from ocp_viewer import set_port, show

    set_port(port)
    show(*objs, names=names, **kwargs)
