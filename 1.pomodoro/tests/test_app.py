import pytest
from app import app


@pytest.fixture
def client():
    """Flaskテストクライアントを返すフィクスチャ。"""
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client


class TestIndexRoute:
    """GET / ルートのテスト。"""

    def test_status_code_is_200(self, client):
        """GETリクエストで200が返ること。"""
        response = client.get("/")
        assert response.status_code == 200

    def test_content_type_is_html(self, client):
        """レスポンスのContent-TypeがHTMLであること。"""
        response = client.get("/")
        assert "text/html" in response.content_type

    def test_page_title_contains_pomodoro(self, client):
        """ページタイトルにポモドーロタイマーが含まれること。"""
        response = client.get("/")
        assert "ポモドーロタイマー" in response.data.decode("utf-8")

    def test_response_is_not_empty(self, client):
        """レスポンスボディが空でないこと。"""
        response = client.get("/")
        assert len(response.data) > 0

    def test_charset_is_utf8(self, client):
        """レスポンスのContent-TypeにUTF-8が含まれること。"""
        response = client.get("/")
        assert "utf-8" in response.content_type.lower()

    def test_response_includes_css_link(self, client):
        """レスポンスにCSSファイルへのリンクが含まれること。"""
        response = client.get("/")
        assert "style.css" in response.data.decode("utf-8")


class TestNotFoundRoute:
    """存在しないルートへのアクセスのテスト。"""

    def test_unknown_route_returns_404(self, client):
        """存在しないパスへのGETリクエストで404が返ること。"""
        response = client.get("/not-exist")
        assert response.status_code == 404


class TestAppConfig:
    """Flaskアプリ設定のテスト。"""

    def test_app_is_created(self):
        """Flaskアプリが正常に生成されていること。"""
        assert app is not None

    def test_testing_mode_can_be_enabled(self):
        """テスティングモードを有効にできること。"""
        app.config["TESTING"] = True
        assert app.config["TESTING"] is True
