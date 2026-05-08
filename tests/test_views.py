from plone import api
from ims.users.interfaces import IControlPanel


class TestUsersCan:
    def test_login_url(self, portal):
        view = api.content.get_view("get_login_url", context=portal)
        assert view() == "https://nohost"
        api.portal.set_registry_record(name="enabled", value=False, interface=IControlPanel)
        assert view() == "http://nohost/plone/login_form"
