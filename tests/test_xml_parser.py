"""Tests for OSMER XML parser."""

from custom_components.osmer_fvg.api.xml_parser import (
    _parse_date,
    _parse_temp_value,
    parse_osmer_forecast_xml,
)


class TestParseTempValue:
    """Tests for temperature value parsing."""

    def test_parse_simple_value(self) -> None:
        """Test parsing simple temperature value."""
        assert _parse_temp_value("25.5") == 25.5
        assert _parse_temp_value("20") == 20.0

    def test_parse_range_value(self) -> None:
        """Test parsing temperature range."""
        assert _parse_temp_value("20/23") == 21.5
        assert _parse_temp_value("18 / 22") == 20.0
        assert _parse_temp_value("20/25/30") == 25.0

    def test_parse_none_values(self) -> None:
        """Test parsing none/empty values."""
        assert _parse_temp_value(None) is None
        assert _parse_temp_value("") is None
        assert _parse_temp_value("   ") is None

    def test_parse_special_values(self) -> None:
        """Test parsing special placeholder values."""
        assert _parse_temp_value("n.d.") is None
        assert _parse_temp_value("N.D.") is None
        assert _parse_temp_value("-") is None
        assert _parse_temp_value("nd") is None
        assert _parse_temp_value("n/a") is None
        assert _parse_temp_value("null") is None

    def test_parse_invalid_values(self) -> None:
        """Test parsing invalid values."""
        assert _parse_temp_value("abc") is None
        assert _parse_temp_value("20/abc") is None
        assert _parse_temp_value("20/") is None


class TestParseDate:
    """Tests for date parsing."""

    def test_parse_dd_mm_yyyy(self) -> None:
        """Test parsing DD-MM-YYYY format."""
        assert _parse_date("11-08-2024") == "2024-08-11"
        assert _parse_date("01-01-2024") == "2024-01-01"

    def test_parse_dd_mm_yyyy_slash(self) -> None:
        """Test parsing DD/MM/YYYY format."""
        assert _parse_date("11/08/2024") == "2024-08-11"
        assert _parse_date("01/01/2024") == "2024-01-01"

    def test_parse_yyyy_mm_dd(self) -> None:
        """Test parsing YYYY-MM-DD format."""
        assert _parse_date("2024-08-11") == "2024-08-11"
        assert _parse_date("2024/08/11") == "2024-08-11"

    def test_parse_iso_datetime(self) -> None:
        """Test parsing ISO datetime format."""
        assert _parse_date("2024-08-11T12:00:00+00:00") == "2024-08-11T12:00:00+00:00"
        assert _parse_date("2024-08-11T12:00:00") == "2024-08-11T12:00:00"

    def test_parse_none_empty(self) -> None:
        """Test parsing none/empty values."""
        assert _parse_date(None) == ""
        assert _parse_date("") == ""
        assert _parse_date("   ") == ""

    def test_parse_unknown_format(self) -> None:
        """Test parsing unknown format returns original."""
        assert _parse_date("unknown") == "unknown"
        assert _parse_date("11-08") == "11-08"


class TestParseOsmerForecastXml:
    """Tests for OSMER XML forecast parsing."""

    def test_parse_valid_xml_z1(self) -> None:
        """Test parsing valid XML for zone Z1."""
        xml_content = """<?xml version="1.0" encoding="UTF-8"?>
        <root>
            <scadenza data_validita="11-08-2024">
                <zona id="Z1" nome="Monti">
                    <TMIN>15/18</TMIN>
                    <TMAX>25/28</TMAX>
                    <CIELO_DESCRIZIONE>Sereno</CIELO_DESCRIZIONE>
                    <PROBABILITAPRECIPITAZIONI>10</PROBABILITAPRECIPITAZIONI>
                </zona>
            </scadenza>
        </root>
        """
        forecasts = parse_osmer_forecast_xml(xml_content, "Z1")
        assert len(forecasts) == 1
        assert forecasts[0].date == "2024-08-11"
        assert forecasts[0].condition == "sunny"
        assert forecasts[0].temp_min == 16.5  # (15+18)/2
        assert forecasts[0].temp_max == 26.5  # (25+28)/2
        assert forecasts[0].precipitation_probability == 10

    def test_parse_valid_xml_z3(self) -> None:
        """Test parsing valid XML for zone Z3."""
        xml_content = """<?xml version="1.0" encoding="UTF-8"?>
        <root>
            <scadenza data_validita="12/08/2024">
                <zona id="Z3" nome="Bassa Pianura">
                    <TMIN>18</TMIN>
                    <TMAX>30</TMAX>
                    <EVOLUZIONE24_DESCRIZIONE>Nuvoloso</EVOLUZIONE24_DESCRIZIONE>
                    <PROBABILITAPRECIPITAZIONI>40</PROBABILITAPRECIPITAZIONI>
                    <TESTO>Cielo nuvoloso</TESTO>
                </zona>
            </scadenza>
        </root>
        """
        forecasts = parse_osmer_forecast_xml(xml_content, "Z3")
        assert len(forecasts) == 1
        assert forecasts[0].date == "2024-08-12"
        assert forecasts[0].condition == "cloudy"
        assert forecasts[0].temp_min == 18.0
        assert forecasts[0].temp_max == 30.0
        assert forecasts[0].precipitation_probability == 40
        assert forecasts[0].summary == "Cielo nuvoloso"

    def test_parse_xml_with_multiple_zones(self) -> None:
        """Test parsing XML with multiple zones, selecting correct one."""
        xml_content = """<?xml version="1.0" encoding="UTF-8"?>
        <root>
            <scadenza data_validita="11-08-2024">
                <zona id="Z1" nome="Monti">
                    <TMIN>10</TMIN>
                    <TMAX>20</TMAX>
                    <CIELO_DESCRIZIONE>Sereno</CIELO_DESCRIZIONE>
                </zona>
                <zona id="Z3" nome="Bassa Pianura">
                    <TMIN>15</TMIN>
                    <TMAX>25</TMAX>
                    <CIELO_DESCRIZIONE>Poco nuvoloso</CIELO_DESCRIZIONE>
                </zona>
            </scadenza>
        </root>
        """
        forecasts_z3 = parse_osmer_forecast_xml(xml_content, "Z3")
        assert len(forecasts_z3) == 1
        assert forecasts_z3[0].temp_min == 15.0
        assert forecasts_z3[0].condition == "partlycloudy"

    def test_parse_xml_with_f_zone(self) -> None:
        """Test parsing XML with F zone (should match Z zone)."""
        xml_content = """<?xml version="1.0" encoding="UTF-8"?>
        <root>
            <scadenza data_validita="11-08-2024">
                <zona id="F3" nome="Bassa Pianura">
                    <TMIN>15</TMIN>
                    <TMAX>25</TMAX>
                    <CIELO_DESCRIZIONE>Sereno</CIELO_DESCRIZIONE>
                </zona>
            </scadenza>
        </root>
        """
        # Should match F3 with Z3
        forecasts = parse_osmer_forecast_xml(xml_content, "Z3")
        assert len(forecasts) == 1

    def test_parse_empty_xml(self) -> None:
        """Test parsing empty XML."""
        forecasts = parse_osmer_forecast_xml("", "Z1")
        assert forecasts == []

    def test_parse_invalid_xml(self) -> None:
        """Test parsing invalid XML."""
        forecasts = parse_osmer_forecast_xml("<invalid>", "Z1")
        assert forecasts == []

    def test_parse_html_response(self) -> None:
        """Test that HTML responses are ignored."""
        html_content = "<html><body>Not found</body></html>"
        forecasts = parse_osmer_forecast_xml(html_content, "Z1")
        assert forecasts == []

    def test_parse_empty_target_zone(self) -> None:
        """Test parsing with empty target zone."""
        xml_content = """<?xml version="1.0" encoding="UTF-8"?>
        <root>
            <scadenza data_validita="11-08-2024">
                <zona id="Z1" nome="Monti">
                    <TMIN>10</TMIN>
                    <TMAX>20</TMAX>
                </zona>
            </scadenza>
        </root>
        """
        forecasts = parse_osmer_forecast_xml(xml_content, "")
        assert forecasts == []

    def test_parse_missing_elements(self) -> None:
        """Test parsing XML with missing elements."""
        xml_content = """<?xml version="1.0" encoding="UTF-8"?>
        <root>
            <scadenza data_validita="11-08-2024">
                <zona id="Z1" nome="Monti">
                </zona>
            </scadenza>
        </root>
        """
        forecasts = parse_osmer_forecast_xml(xml_content, "Z1")
        # Should still create entry if there's a matching zone
        assert len(forecasts) == 0  # No data, so no forecast added

    def test_parse_iso_date_in_xml(self) -> None:
        """Test parsing XML with ISO date format."""
        xml_content = """<?xml version="1.0" encoding="UTF-8"?>
        <root>
            <scadenza data_validita="2024-08-11T12:00:00+00:00">
                <zona id="Z1" nome="Monti">
                    <TMIN>10</TMIN>
                    <TMAX>20</TMAX>
                </zona>
            </scadenza>
        </root>
        """
        forecasts = parse_osmer_forecast_xml(xml_content, "Z1")
        assert len(forecasts) == 1
        assert forecasts[0].date == "2024-08-11T12:00:00+00:00"
