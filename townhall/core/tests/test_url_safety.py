import socket
from unittest.mock import patch

from django.test import TestCase

from core.url_safety import is_safe_url


def _addrinfo(ip: str):
    return [(socket.AF_INET, socket.SOCK_STREAM, 6, "", (ip, 0))]


# is_safe_url guards against SSRF (Server-Side Request Forgery): an attack where
# an adversary passes a private/internal IP as a URL, causing the server to fetch
# it on their behalf — bypassing the network boundary that normally blocks outside
# access to internal resources (databases, cloud metadata endpoints, etc.).
#
# The function resolves the hostname to an IP *before* fetching and rejects anything
# that falls outside the public internet. Tests below cover each rejection category.
class TestIsSafeUrl(TestCase):
    @patch("core.url_safety.socket.getaddrinfo")
    def test_public_https_url_is_safe(self, mock_getaddrinfo):
        # Sanity check: a normal public URL must be allowed, otherwise the
        # link-preview feature is broken for legitimate use.
        mock_getaddrinfo.return_value = _addrinfo("93.184.216.34")

        # Act
        result = is_safe_url("https://example.com/path")

        # Assert
        self.assertTrue(result)

    def test_disallowed_scheme_is_rejected(self):
        # Only http/https make sense for link previews.
        # file:// would let an attacker read arbitrary files on the server
        # (e.g. file:///etc/passwd); ftp:// has no legitimate preview use.
        # Rejected before DNS resolution — no @patch needed.
        self.assertFalse(is_safe_url("ftp://example.com"))
        self.assertFalse(is_safe_url("file:///etc/passwd"))

    def test_missing_hostname_is_rejected(self):
        # Without a hostname there is nothing to resolve, so safety cannot be
        # verified. Rejected at URL-parse time — no DNS call is made, hence no @patch.
        self.assertFalse(is_safe_url("https:///path-only"))

    @patch("core.url_safety.socket.getaddrinfo")
    def test_loopback_address_is_rejected(self, mock_getaddrinfo):
        # 127.0.0.1 points to the server itself. An attacker could use it to
        # reach internal APIs running on other ports of the same machine.
        # Rejection is based on the *resolved IP*, not the hostname string,
        # so aliases like "localhost" are also caught.
        mock_getaddrinfo.return_value = _addrinfo("127.0.0.1")

        # Act
        result = is_safe_url("https://localhost/")

        # Assert
        self.assertFalse(result)

    @patch("core.url_safety.socket.getaddrinfo")
    def test_private_range_address_is_rejected(self, mock_getaddrinfo):
        # 10.x.x.x (and 172.16–31.x.x, 192.168.x.x) are private network ranges
        # unreachable from the public internet but reachable from within the server's
        # network — e.g. a database or internal admin tool on the same VPC.
        # A domain like "internal.example.com" can resolve to such an IP, so we
        # check the IP, not the domain name.
        mock_getaddrinfo.return_value = _addrinfo("10.0.0.5")

        # Act
        result = is_safe_url("https://internal.example.com/")

        # Assert
        self.assertFalse(result)

    @patch("core.url_safety.socket.getaddrinfo")
    def test_cloud_metadata_link_local_address_is_rejected(self, mock_getaddrinfo):
        # 169.254.169.254 is the AWS instance metadata endpoint. It is only
        # reachable from within the EC2 instance itself and returns the IAM role
        # credentials attached to that instance — a prime SSRF target.
        # An attacker can point any domain at this IP, so we reject on IP, not name.
        mock_getaddrinfo.return_value = _addrinfo("169.254.169.254")

        # Act
        result = is_safe_url("https://metadata.example.com/")

        # Assert
        self.assertFalse(result)

    @patch("core.url_safety.socket.getaddrinfo")
    def test_mixed_public_and_private_resolution_is_rejected(self, mock_getaddrinfo):
        # DNS rebinding attack: a domain returns both a public IP (to pass the check)
        # and a private IP (used for the actual connection). We must reject the URL
        # if *any* resolved address is private — all-or-nothing, not majority-vote.
        mock_getaddrinfo.return_value = [
            (socket.AF_INET, socket.SOCK_STREAM, 6, "", ("93.184.216.34", 0)),
            (socket.AF_INET, socket.SOCK_STREAM, 6, "", ("192.168.1.1", 0)),
        ]

        # Act
        result = is_safe_url("https://example.com/")

        # Assert
        self.assertFalse(result)

    @patch("core.url_safety.socket.getaddrinfo")
    def test_dns_resolution_failure_is_rejected(self, mock_getaddrinfo):
        # If DNS lookup fails we cannot verify the IP, so we default to rejection.
        # "Fail closed" — anything unverifiable is treated as unsafe.
        # socket.gaierror is the exception raised by getaddrinfo on lookup failure;
        # side_effect makes the mock raise it instead of returning a value.
        mock_getaddrinfo.side_effect = socket.gaierror("no such host")

        # Act
        result = is_safe_url("https://does-not-resolve.invalid/")

        # Assert
        self.assertFalse(result)
