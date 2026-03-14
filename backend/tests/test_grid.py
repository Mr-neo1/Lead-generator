"""
Unit tests for the grid coordinate generator.
The geocoder is mocked so these tests run without internet access.
"""

import math
from unittest.mock import MagicMock, patch

import pytest


# ── Helpers ───────────────────────────────────────────────────────────────────

def make_mock_location(lat: float = 30.9, lng: float = 75.85):
    loc = MagicMock()
    loc.latitude = lat
    loc.longitude = lng
    return loc


# ── generate_grid ─────────────────────────────────────────────────────────────

class TestGenerateGrid:
    def _call(self, location_name="Ludhiana", radius_km=10, grid_size="2x2"):
        from grid_generator import generate_grid
        return generate_grid(location_name, radius_km, grid_size)

    def test_returns_correct_number_of_points(self):
        with patch("grid_generator.Nominatim") as mock_nom:
            mock_nom.return_value.geocode.return_value = make_mock_location()
            coords = self._call(grid_size="3x4")
        assert len(coords) == 12  # 3 rows × 4 cols

    def test_square_grid(self):
        with patch("grid_generator.Nominatim") as mock_nom:
            mock_nom.return_value.geocode.return_value = make_mock_location()
            coords = self._call(grid_size="5x5")
        assert len(coords) == 25

    def test_each_point_is_lat_lng_tuple(self):
        with patch("grid_generator.Nominatim") as mock_nom:
            mock_nom.return_value.geocode.return_value = make_mock_location(lat=28.6, lng=77.2)
            coords = self._call(grid_size="2x2")
        for point in coords:
            assert len(point) == 2
            lat, lng = point
            assert isinstance(lat, float)
            assert isinstance(lng, float)

    def test_coords_spread_around_centre(self):
        """Points should bracket the centre lat/lng."""
        centre_lat, centre_lng = 28.6, 77.2
        with patch("grid_generator.Nominatim") as mock_nom:
            mock_nom.return_value.geocode.return_value = make_mock_location(
                lat=centre_lat, lng=centre_lng
            )
            coords = self._call(radius_km=10, grid_size="4x4")

        lats = [c[0] for c in coords]
        lngs = [c[1] for c in coords]
        # There should be points both above AND below the centre latitude
        assert min(lats) < centre_lat < max(lats)
        assert min(lngs) < centre_lng < max(lngs)

    def test_location_not_found_raises_value_error(self):
        with patch("grid_generator.Nominatim") as mock_nom:
            mock_nom.return_value.geocode.return_value = None
            with pytest.raises(ValueError, match="Location not found"):
                self._call(location_name="ZZZ_NONEXISTENT_PLACE")

    def test_larger_radius_spans_more_area(self):
        with patch("grid_generator.Nominatim") as mock_nom:
            mock_nom.return_value.geocode.return_value = make_mock_location()

            coords_small = self._call(radius_km=5, grid_size="2x2")
            coords_large = self._call(radius_km=50, grid_size="2x2")

        span_small = max(c[0] for c in coords_small) - min(c[0] for c in coords_small)
        span_large = max(c[0] for c in coords_large) - min(c[0] for c in coords_large)
        assert span_large > span_small
