import pytest
import responses

from feed_comparison.feeds._http import ResponseTooLargeError, bounded_get


@responses.activate
def test_bounded_get_returns_full_body_when_within_cap():
    payload = b"x" * 1024
    responses.add(responses.GET, "https://example.com/data", body=payload, status=200)

    resp = bounded_get("https://example.com/data", max_bytes=10 * 1024)
    assert resp.status_code == 200
    assert resp.content == payload


@responses.activate
def test_bounded_get_aborts_when_body_exceeds_cap():
    big = b"y" * 4096
    responses.add(responses.GET, "https://example.com/oversized", body=big, status=200)

    with pytest.raises(ResponseTooLargeError) as exc:
        bounded_get("https://example.com/oversized", max_bytes=512)
    assert exc.value.max_bytes == 512
    assert "https://example.com/oversized" in str(exc.value)


@responses.activate
def test_bounded_get_aborts_on_oversized_content_length_header():
    """Even if we never read the body, a declared Content-Length over the cap
    must be rejected up-front."""
    responses.add(
        responses.GET,
        "https://example.com/lying",
        body=b"actually small",
        status=200,
        headers={"Content-Length": str(10**9)},  # 1 GB declared
    )
    with pytest.raises(ResponseTooLargeError):
        bounded_get("https://example.com/lying", max_bytes=1024)


@responses.activate
def test_bounded_get_passes_headers_and_kwargs():
    responses.add(responses.GET, "https://example.com/auth", body=b"ok", status=200)
    resp = bounded_get(
        "https://example.com/auth",
        headers={"X-Test": "yes"},
        max_bytes=1024,
    )
    assert resp.status_code == 200
    # The header reached the recorded request.
    sent = responses.calls[0].request
    assert sent.headers.get("X-Test") == "yes"
