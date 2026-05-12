from plone import api


class TestViews:
    def test_login_url(self, portal):
        view = api.content.get_view("get_login_url", context=portal)
        assert view() == "http://nohost/plone/@@login?came_from=http://nohost"
