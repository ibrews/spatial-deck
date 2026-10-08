#!/usr/bin/env python3
"""Serve the deck for headless passes — concurrent, so it doesn't fake its own bugs.

USE THIS, NOT `python3 -m http.server`. The stdlib one-liner is single-threaded
with a tiny listen backlog, and a headless sweep opens many subresource requests
at once (a slide's images, SVGs and videos together). The server resets the
overflow, so Chrome reports `net::ERR_CONNECTION_RESET` /
`ERR_SOCKET_NOT_CONNECTED` on random assets and the deck renders *blank image
slides* that look exactly like real deck defects.

That misdiagnosis has now cost two separate QA passes (2026-10-07 and
2026-10-08), the second one while building tools/sweep_deck.mjs — four phantom
"broken image" failures that were the server, not the deck. Hence this file:
the fix belongs next to the tool that needs it, not in a note somebody has to
remember to read.

    python3 tools/serve_deck.py                 # port 8000, repo root
    python3 tools/serve_deck.py --port 8411
    python3 tools/serve_deck.py --dir /tmp/some-deck-checkout

Then, in another shell:
    node tools/sweep_deck.mjs http://localhost:8411/ /tmp/sweep 375 812 phone
"""
import argparse
import functools
import os
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer


class DeckServer(ThreadingHTTPServer):
    # The default is 5. A sweep can have dozens of requests in flight for one
    # slide; anything that doesn't fit the backlog is reset, not queued.
    request_queue_size = 256
    daemon_threads = True
    allow_reuse_address = True


class QuietHandler(SimpleHTTPRequestHandler):
    def log_message(self, fmt, *args):  # a sweep makes thousands of these
        pass


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--port", type=int, default=8000)
    ap.add_argument("--dir", default=str(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
    ap.add_argument("--verbose", action="store_true", help="log every request")
    args = ap.parse_args()

    handler = functools.partial(
        SimpleHTTPRequestHandler if args.verbose else QuietHandler, directory=args.dir
    )
    with DeckServer(("127.0.0.1", args.port), handler) as httpd:
        print(f"serving {args.dir} at http://localhost:{args.port}/ "
              f"(threaded, backlog {DeckServer.request_queue_size}) — ctrl-c to stop")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nstopped")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
