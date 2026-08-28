from scripts.config_check import validate_environment


def test_development_configuration_is_valid(monkeypatch, tmp_path):
    data_file = tmp_path / "companies.csv"
    data_file.write_text("company_name,company_rating\nExample,4.2\n", encoding="utf-8")

    monkeypatch.setenv("AMBITIONBOX_DATA_PATH", str(data_file))
    monkeypatch.setenv("AMBITIONBOX_DB_PATH", str(tmp_path / "ambitionbox.db"))
    monkeypatch.delenv("FLASK_DEBUG", raising=False)
    monkeypatch.delenv("FLASK_PORT", raising=False)
    monkeypatch.delenv("FLASK_SECRET_KEY", raising=False)
    monkeypatch.delenv("SECRET_KEY", raising=False)

    result = validate_environment(production=False)

    assert result["valid"] is True
    assert result["port"] == 5000
    assert result["debug"] is False
    assert result["errors"] == []


def test_production_rejects_default_secret_and_debug(monkeypatch):
    monkeypatch.setenv("FLASK_SECRET_KEY", "change-this-in-production")
    monkeypatch.setenv("FLASK_DEBUG", "true")

    result = validate_environment(production=True)

    assert result["valid"] is False
    assert any("FLASK_SECRET_KEY" in item for item in result["errors"])
    assert any("FLASK_DEBUG" in item for item in result["errors"])


def test_invalid_port_is_rejected(monkeypatch):
    monkeypatch.setenv("FLASK_PORT", "70000")

    result = validate_environment(production=False)

    assert result["valid"] is False
    assert any("FLASK_PORT" in item for item in result["errors"])
