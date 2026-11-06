import ipaddress
import socket
from urllib.parse import urlparse

ALLOWED_SCHEMES = {"http", "https"}


def is_safe_url(url: str) -> bool:
    """
    This is the SSRF (Server-Side Request Forgery) gatekeeper. Rejects URLs
    unsuitable for a server-side fetch: non-http(s) schemes, or hostnames
    that resolve to a private/loopback/link-local/reserved/multicast address
    (blocks SSRF against internal services and cloud metadata endpoints).
    The built-in "socket" module is used for DNS resolution; "ipaddress" is
    used for classifying the resulting IP address.
    """
    try:
        parsed = urlparse(url)
    except ValueError:
        return False

    if parsed.scheme not in ALLOWED_SCHEMES:
        return False

    hostname = parsed.hostname
    if not hostname:
        return False

    try:
        # DNS resolution: look up IP address(es) for this hostname.
        addr_infos = socket.getaddrinfo(hostname, None)
    except socket.gaierror:
        return False

    if not addr_infos:
        return False

    for info in addr_infos:
        ip_str = info[4][0]
        try:
            ip = ipaddress.ip_address(ip_str)
        except ValueError:
            return False

        if (
            ip.is_private
            or ip.is_loopback
            or ip.is_link_local
            or ip.is_reserved
            or ip.is_multicast
            or ip.is_unspecified
        ):
            return False

    return True
