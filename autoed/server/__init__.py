import argparse

import uvicorn


def run():
    parser = argparse.ArgumentParser(description="Start the AutoED server")
    parser.add_argument(
        "--host",
        help="Listen for incoming connections on a specific interface (IP address or hostname; default: all)",
        default="0.0.0.0",
    )
    parser.add_argument(
        "--port",
        help="Listen for incoming TCP connections on this port (default: 8001)",
        type=int,
        default=8000,
    )
    args = parser.parse_args()

    config = uvicorn.Config(
        "autoed.server.main:app",
        host=args.host,
        port=args.port,
        log_config=None,
        ws_ping_interval=300,
        ws_ping_timeout=300,
    )

    _running_server = uvicorn.Server(config=config)
    _running_server.run()
