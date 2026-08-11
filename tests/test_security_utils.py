from __future__ import annotations

import unittest

from scripts.security_utils import canonical_http_url, parse_http_target, redact, redact_url, url_allowed


class SecurityUtilsTests(unittest.TestCase):
    def test_canonical_url_removes_default_port(self) -> None:
        self.assertEqual(canonical_http_url("HTTPS://Example.COM:443/a"), "https://example.com/a")

    def test_canonical_ipv6_keeps_brackets(self) -> None:
        self.assertEqual(canonical_http_url("https://[::1]:443/x"), "https://[::1]/x")

    def test_userinfo_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            parse_http_target("https://allowed.example@attacker.example/x")

    def test_exact_host_is_allowed(self) -> None:
        self.assertTrue(url_allowed("https://api.example.test/v1/a", ["https://api.example.test/v1"]))

    def test_lookalike_host_is_rejected(self) -> None:
        self.assertFalse(url_allowed("https://api.example.test.evil.invalid/x", ["https://api.example.test"]))

    def test_path_boundary_is_enforced(self) -> None:
        self.assertFalse(url_allowed("https://api.example.test/api-v2", ["https://api.example.test/api"]))

    def test_string_allowlist_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            url_allowed("https://api.example.test", "https://api.example.test")

    def test_empty_allowlist_entry_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            url_allowed("https://api.example.test", [""])

    def test_encoded_path_separator_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            parse_http_target("https://api.example.test/a%2fb")

    def test_double_encoded_traversal_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            parse_http_target("https://api.example.test/safe/%252e%252e/admin")

    def test_deeply_encoded_traversal_is_rejected(self) -> None:
        encoded = "%2e"
        for _ in range(20):
            encoded = encoded.replace("%", "%25")
        with self.assertRaises(ValueError):
            parse_http_target(f"https://api.example.test/safe/{encoded}/admin")

    def test_port_zero_is_not_rewritten_to_default_port(self) -> None:
        with self.assertRaises(ValueError):
            parse_http_target("http://api.example.test:0/")

    def test_value_based_secrets_are_redacted(self) -> None:
        output = redact({"note": "Authorization: Bearer TOPSECRET", "body": "password=hunter2"})
        self.assertNotIn("TOPSECRET", str(output))
        self.assertNotIn("hunter2", str(output))

    def test_sensitive_query_value_is_redacted(self) -> None:
        output = redact("https://api.example.test/x?token=TOPSECRET&mode=safe")
        self.assertNotIn("TOPSECRET", str(output))
        self.assertIn("mode=safe", str(output))

    def test_variant_secret_query_names_are_redacted(self) -> None:
        output = redact_url(
            "https://example.test/x?x-api-key=TOPSECRET&client_secret=TOPSECRET&sessionid=TOPSECRET"
        )
        self.assertNotIn("TOPSECRET", output)

    def test_secret_like_path_segments_are_redacted(self) -> None:
        output = redact_url("https://example.test/api/TOPSECRET/token")
        self.assertNotIn("TOPSECRET", output)


if __name__ == "__main__":
    unittest.main()
