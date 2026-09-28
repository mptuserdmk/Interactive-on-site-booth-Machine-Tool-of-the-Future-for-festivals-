"""
Настройки и URL на QR-кодах (H11), вспомогательные детали конфигурации.
"""
import socket

import pytest

pytestmark = pytest.mark.unit


@pytest.mark.regression
def test_base_url_respects_port():
    """H11: BASE_URL захардкожен на :8000 и игнорирует PORT → QR на карточках битый."""
    from app.config.settings import Settings
    s = Settings(_env_file=None, PORT=8080, LOCAL_IP="192.168.0.10")
    assert s.BASE_URL == "http://192.168.0.10:8080"


def test_explicit_base_url_wins():
    from app.config.settings import Settings
    s = Settings(_env_file=None, BASE_URL="https://kiosk.example.org")
    assert s.BASE_URL == "https://kiosk.example.org"


@pytest.mark.regression
def test_local_ip_without_default_route_uses_interface_address(monkeypatch):
    """H11: без маршрута до 8.8.8.8 get_local_ip() отдаёт 127.0.0.1 → на карточках печатается 127.0.0.1,
    хотя у ПК есть адрес в Wi-Fi площадки."""
    from app.config import settings as settings_mod

    class NoRouteSocket:
        def __init__(self, *a, **k):
            pass

        def settimeout(self, *_):
            pass

        def connect(self, *_):
            raise OSError("Network is unreachable")

        def getsockname(self):
            return ("0.0.0.0", 0)

        def close(self):
            pass

    monkeypatch.setattr(settings_mod.socket, "socket", NoRouteSocket)
    monkeypatch.setattr(settings_mod.socket, "gethostbyname_ex",
                        lambda host: (host, [], ["127.0.0.1", "169.254.10.2", "192.168.4.23"]))
    assert settings_mod.get_local_ip() == "192.168.4.23"


def test_local_ip_real_machine():
    """Факт на стенде разработки: какой IP попадёт в QR прямо сейчас."""
    from app.config.settings import get_local_ip
    ip = get_local_ip()
    print(f"\n[H11] get_local_ip() на этой машине = {ip}")
    socket.inet_aton(ip)


@pytest.mark.regression
async def test_health_warns_when_qr_url_is_loopback(client, monkeypatch):
    from app.config.settings import settings
    monkeypatch.setattr(settings, "LOCAL_IP", "127.0.0.1")
    monkeypatch.setattr(settings, "BASE_URL", "http://127.0.0.1:8000")
    net = (await client.get("/api/health")).json()["diagnostics"]["network"]
    assert net.get("qr_url_ok") is False, net


def test_card_url_uses_base_url(monkeypatch):
    from app.composition.qr import get_digital_card_url
    from app.config.settings import settings
    monkeypatch.setattr(settings, "BASE_URL", "http://10.0.0.5:9000")
    assert get_digital_card_url("sess_x") == "http://10.0.0.5:9000/card/sess_x"
