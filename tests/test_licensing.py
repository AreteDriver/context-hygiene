"""Tests for context_hygiene.licensing."""

from __future__ import annotations

from unittest.mock import patch

import pytest

from context_hygiene.exceptions import LicenseError
from context_hygiene.licensing import (
    _ENV_VAR,
    _PREFIX,
    _SALT,
    MAX_FREE_AUDITS_PER_MONTH,
    LicenseInfo,
    Tier,
    _compute_checksum,
    generate_key,
    get_license,
    validate_key,
)


class TestTier:
    def test_values(self):
        assert Tier.FREE == "free"
        assert Tier.PRO == "pro"


class TestLicenseInfo:
    def test_free(self):
        info = LicenseInfo(tier=Tier.FREE)
        assert not info.is_pro

    def test_pro(self):
        info = LicenseInfo(tier=Tier.PRO, key="test")
        assert info.is_pro
        assert info.key == "test"


class TestComputeChecksum:
    def test_deterministic(self):
        c1 = _compute_checksum("TEST-KEY0")
        c2 = _compute_checksum("TEST-KEY0")
        assert c1 == c2

    def test_different_body(self):
        c1 = _compute_checksum("TEST-KEY0")
        c2 = _compute_checksum("TEST-KEY1")
        assert c1 != c2

    def test_length(self):
        c = _compute_checksum("TEST-KEY0")
        assert len(c) == 16

    def test_uppercase(self):
        c = _compute_checksum("TEST-KEY0")
        assert c == c.upper()


class TestGenerateKey:
    def test_default(self):
        key = generate_key()
        assert key.startswith(f"{_PREFIX}-")
        parts = key.split("-")
        assert len(parts) == 4

    def test_custom_body(self):
        key = generate_key("CUST-BODY")
        assert "CUST-BODY" in key

    def test_validates(self):
        key = generate_key()
        info = validate_key(key)
        assert info.is_pro


class TestValidateKey:
    def test_valid_key(self):
        key = generate_key("ABCD-EF01")
        info = validate_key(key)
        assert info.tier == Tier.PRO
        assert info.key == key

    def test_empty_key(self):
        with pytest.raises(LicenseError, match="Empty"):
            validate_key("")

    def test_wrong_segments(self):
        with pytest.raises(LicenseError, match="segments"):
            validate_key("CTHG-XXXX-XXXX")

    def test_wrong_prefix(self):
        with pytest.raises(LicenseError, match="prefix"):
            validate_key("ASPD-XXXX-XXXX-XXXX")

    def test_bad_checksum(self):
        with pytest.raises(LicenseError, match="checksum"):
            validate_key("CTHG-XXXX-XXXX-0000000000000000")

    def test_whitespace_stripped(self):
        key = generate_key()
        info = validate_key(f"  {key}  ")
        assert info.is_pro

    def test_case_insensitive_checksum(self):
        key = generate_key("ABCD-EF01")
        parts = key.split("-")
        parts[3] = parts[3].lower()
        info = validate_key("-".join(parts))
        assert info.is_pro


class TestGetLicense:
    def test_no_env_var(self):
        with patch.dict("os.environ", {}, clear=True):
            info = get_license()
            assert info.tier == Tier.FREE

    def test_valid_key(self):
        key = generate_key()
        with patch.dict("os.environ", {_ENV_VAR: key}):
            info = get_license()
            assert info.tier == Tier.PRO

    def test_invalid_key_falls_back(self):
        with patch.dict("os.environ", {_ENV_VAR: "invalid-key"}):
            info = get_license()
            assert info.tier == Tier.FREE

    def test_env_var_name(self):
        assert _ENV_VAR == "CONTEXT_HYGIENE_LICENSE"


class TestConstants:
    def test_prefix(self):
        assert _PREFIX == "CTHG"

    def test_salt(self):
        assert _SALT == "context-hygiene-v1"

    def test_free_limit(self):
        assert MAX_FREE_AUDITS_PER_MONTH == 10
