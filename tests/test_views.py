import pytest
from ims.sso.configs import AUTHENTICATED_KEY, DISABLED_STATUS, INACTIVE_STATUS
from ims.sso.interfaces import ISSOSettings
from plone import api
from plone.testing import zope
from zope.annotation.interfaces import IAnnotations


class TestViews:
    username = "siteadmin"
    email = "noreply@nohost.com"
    idp = "testdomain"
    user = None

    @pytest.fixture(autouse=True)
    def setup_users(self, http_request, sso):
        self.user = api.user.create(username=self.username, email=self.email)
        sso.set_login_name(user_id=self.username, login_name=f"{self.username}@{self.idp}")
        api.portal.set_registry_record(interface=ISSOSettings, name="show_auth_unauth", value=True)

        http_request.environ[sso.get_setting("shib_header_user")] = self.username
        http_request.environ[sso.get_setting("shib_header_idp")] = self.idp
        http_request[sso.get_setting("shib_header_email")] = self.email

    def test_login_url(self, portal):
        view = api.content.get_view("get_login_url", context=portal)
        assert view() == "http://nohost/plone/@@login?came_from=http://nohost"

    def test_viewlet_auth_unauth(self, portal):
        zope.logout()

        view = api.content.get_view(context=portal, name="view")
        content = view()
        assert "There is not an active account" in content

    def test_viewlet_inactive(self, portal, http_request):
        annotations = IAnnotations(http_request)
        annotations[AUTHENTICATED_KEY] = self.username
        zope.logout()  # we aren't going through the plugins here, or they would not have been logged
        self.user.setMemberProperties({"active": INACTIVE_STATUS})

        view = api.content.get_view(context=portal, name="view")
        content = view()
        assert "Your account has been locked due to inactivity" in content

    def test_viewlet_disabled(self, portal, http_request):
        annotations = IAnnotations(http_request)
        annotations[AUTHENTICATED_KEY] = self.username
        zope.logout()
        self.user.setMemberProperties({"active": DISABLED_STATUS})

        view = api.content.get_view(context=portal, name="view")
        content = view()

        assert "Your account has been disabled" in content
