"""Tests for OSMER forecast zone resolver."""

from custom_components.osmer_fvg.forecast_zone import get_osmer_zone


class TestGetOsmerZone:
    """Tests for forecast zone determination."""

    def test_high_altitude_is_z1(self) -> None:
        """Test that high altitude locations are zone Z1 (Monti)."""
        # Any altitude >= 500m should be Z1
        assert get_osmer_zone(46.0, 13.0, 500.0) == "Z1"
        assert get_osmer_zone(46.0, 13.0, 600.0) == "Z1"
        assert get_osmer_zone(46.0, 13.0, 1000.0) == "Z1"

    def test_low_altitude_uses_centroids(self) -> None:
        """Test that low altitude locations use centroid distance."""
        # These should be determined by distance to centroids
        assert get_osmer_zone(46.0, 13.0, 100.0) in ["Z1", "Z2", "Z3", "Z4"]
        assert get_osmer_zone(45.8, 13.2, 50.0) in ["Z1", "Z2", "Z3", "Z4"]

    def test_z1_centroid_area(self) -> None:
        """Test coordinates near Z1 centroid (Monti)."""
        # Z1 centroid: 46.40, 12.90
        # Near coordinates should be Z1
        assert get_osmer_zone(46.40, 12.90, 400.0) == "Z1"

    def test_z2_centroid_area(self) -> None:
        """Test coordinates near Z2 centroid (Alta Pianura)."""
        # Z2 centroid: 46.10, 13.10
        # Low altitude near Z2 centroid should be Z2
        assert get_osmer_zone(46.10, 13.10, 100.0) == "Z2"

    def test_z3_centroid_area(self) -> None:
        """Test coordinates near Z3 centroid (Bassa Pianura)."""
        # Z3 centroid: 45.85, 13.15
        assert get_osmer_zone(45.85, 13.15, 50.0) == "Z3"

    def test_z4_centroid_area(self) -> None:
        """Test coordinates near Z4 centroid (Costa e Carso)."""
        # Z4 centroid: 45.70, 13.60
        assert get_osmer_zone(45.70, 13.60, 20.0) == "Z4"

    def test_udine_area(self) -> None:
        """Test Udine coordinates (should be Z2 - Alta Pianura)."""
        # Udine is approximately at 46.06, 13.23
        zone = get_osmer_zone(46.06, 13.23, 100.0)
        assert zone == "Z2"

    def test_trieste_area(self) -> None:
        """Test Trieste coordinates (should be Z4 - Costa e Carso)."""
        # Trieste is approximately at 45.65, 13.78
        zone = get_osmer_zone(45.65, 13.78, 10.0)
        assert zone == "Z4"

    def test_tolmezzo_area(self) -> None:
        """Test Tolmezzo coordinates (should be Z1 - Monti)."""
        # Tolmezzo is approximately at 46.39, 12.78, altitude ~300m
        # But altitude < 500, so uses centroid
        zone = get_osmer_zone(46.39, 12.78, 300.0)
        assert zone == "Z1"

    def test_altitude_override(self) -> None:
        """Test that altitude >= 500 overrides centroid distance."""
        # Even if coordinates are near Z3 centroid, high altitude should be Z1
        assert get_osmer_zone(45.85, 13.15, 500.0) == "Z1"
        assert get_osmer_zone(45.85, 13.15, 501.0) == "Z1"

    def test_edge_altitude(self) -> None:
        """Test boundary altitude value."""
        # Exactly 500m should be Z1
        assert get_osmer_zone(46.0, 13.0, 500.0) == "Z1"
        # Just below 500m should use centroid
        zone = get_osmer_zone(46.0, 13.0, 499.0)
        assert zone in ["Z2", "Z3", "Z4"]  # Depends on which centroid is closest
