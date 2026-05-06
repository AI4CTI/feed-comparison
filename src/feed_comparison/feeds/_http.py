"""Shared HTTP helpers for feed integrations.

The main entry point is :func:`bounded_get`, a thin wrapper around
``requests.get`` that streams the response and aborts if the body grows
past a configurable limit. This protects the tool from
denial-of-service via memory exhaustion when an upstream feed (or a
proxy in front of it) returns a multi-gigabyte payload.
"""

from __future__ import annotations

import logging

import requests

_log = logging.getLogger(__name__)

_DEFAULT_MAX_RESPONSE_BYTES = 256 * 1024 * 1024  # 256 MiB
_CHUNK_SIZE = 64 * 1024  # 64 KiB


class ResponseTooLargeError(RuntimeError):
    """Raised when a remote response exceeds the configured byte cap."""

    def __init__(self, url, max_bytes):
        self.url = url
        self.max_bytes = max_bytes
        super().__init__(f"Response from {url} exceeded the {max_bytes:_} byte cap; aborting")


def bounded_get(url, *, max_bytes=_DEFAULT_MAX_RESPONSE_BYTES, timeout=120, **kwargs):
    """``requests.get`` with a hard cap on the response body size.

    Streams the response and accumulates it into ``resp.content`` so the
    caller can use ``resp.text`` / ``resp.json()`` exactly as with a normal
    blocking ``requests.get``. The cap is enforced both via the
    ``Content-Length`` header (if the server provides it) and incrementally
    while reading the body, so an honest server doesn't waste bandwidth and
    a misbehaving one doesn't OOM the client.

    Raises:
        ResponseTooLargeError: if the response declares (or grows past)
            ``max_bytes``.

    The caller is still responsible for ``resp.raise_for_status()`` if
    they want HTTP error codes to bubble up.
    """
    resp = requests.get(url, stream=True, timeout=timeout, **kwargs)
    try:
        declared = resp.headers.get("Content-Length")
        if declared is not None:
            try:
                if int(declared) > max_bytes:
                    raise ResponseTooLargeError(url, max_bytes)
            except ValueError:
                # Content-Length not an integer; ignore and fall back to streaming.
                pass

        chunks: list[bytes] = []
        size = 0
        for chunk in resp.iter_content(chunk_size=_CHUNK_SIZE):
            if not chunk:
                continue
            size += len(chunk)
            if size > max_bytes:
                raise ResponseTooLargeError(url, max_bytes)
            chunks.append(chunk)

        # Materialise the body so the rest of the codebase can keep using
        # the standard `resp.content` / `resp.text` / `resp.json()` API.
        resp._content = b"".join(chunks)
        resp._content_consumed = True
    finally:
        resp.close()
    return resp
