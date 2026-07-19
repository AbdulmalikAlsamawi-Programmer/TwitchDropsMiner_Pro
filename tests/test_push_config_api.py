import json
import pytest


def test_get_push_config_defaults(monkeypatch, tmp_path):
    import src.web.app as app_module

    monkeypatch.setattr(app_module, "_WEB_CONFIG_FILE", tmp_path / "web_config.json")
    monkeypatch.setattr(app_module, "_SHARED_WEB_CONFIG_FILE", tmp_path / "shared_web_config.json")
    result = app_module._get_push_config()
    assert result == {
        "push_notifications_enabled": False,
        "push_sound_enabled": True,
        "campaign_end_alerts_enabled": True,
        "store_tab": {
            "tagline": "",
            "description": "",
            "shop_btn": "",
            "discord_btn": "",
            "shop_url": "",
            "discord_url": "",
        },
    }


def test_get_push_config_persisted(monkeypatch, tmp_path):
    import src.web.app as app_module
    cfg_file = tmp_path / "web_config.json"
    cfg_file.write_text(json.dumps({"push_notifications_enabled": True, "push_sound_enabled": False}))
    monkeypatch.setattr(app_module, "_WEB_CONFIG_FILE", cfg_file)
    result = app_module._get_push_config()
    assert result["push_notifications_enabled"] is True
    assert result["push_sound_enabled"] is False
