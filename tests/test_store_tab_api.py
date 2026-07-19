import json

import pytest


def test_get_store_tab_config_defaults(monkeypatch, tmp_path):
    import src.web.app as app_module

    monkeypatch.setattr(app_module, "_SHARED_WEB_CONFIG_FILE", tmp_path / "web_config.json")
    result = app_module._get_store_tab_config()
    assert result == {
        "tagline": "",
        "description": "",
        "shop_btn": "",
        "discord_btn": "",
        "shop_url": "",
        "discord_url": "",
    }


def test_get_store_tab_config_persisted(monkeypatch, tmp_path):
    import src.web.app as app_module

    cfg_file = tmp_path / "web_config.json"
    cfg_file.write_text(
        json.dumps(
            {
                "store_tab": {
                    "tagline": "Custom tagline",
                    "description": "Custom description",
                    "shop_btn": "Shop",
                    "discord_btn": "Discord",
                }
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(app_module, "_SHARED_WEB_CONFIG_FILE", cfg_file)
    result = app_module._get_store_tab_config()
    assert result["tagline"] == "Custom tagline"
    assert result["description"] == "Custom description"
    assert result["shop_btn"] == "Shop"
    assert result["discord_btn"] == "Discord"


@pytest.mark.asyncio
async def test_set_store_tab_config(monkeypatch, tmp_path):
    import src.web.app as app_module
    from src.web.app import StoreTabUpdate, set_store_tab

    cfg_file = tmp_path / "web_config.json"
    static_dir = tmp_path / "web" / "static"
    monkeypatch.setattr(app_module, "_SHARED_WEB_CONFIG_FILE", cfg_file)
    monkeypatch.setattr(app_module, "WEB_DIR", tmp_path / "web")

    result = await set_store_tab(
        StoreTabUpdate(
            tagline="Hello",
            description="World",
            shop_btn="Store",
            discord_btn="Join",
        )
    )
    assert result["ok"] is True
    assert result["tagline"] == "Hello"
    saved = json.loads(cfg_file.read_text(encoding="utf-8"))
    assert saved["store_tab"]["description"] == "World"
    static_file = static_dir / "store_tab.json"
    assert json.loads(static_file.read_text(encoding="utf-8"))["shop_btn"] == "Store"
