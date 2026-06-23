from ims.sso.interfaces import ISSOSettings
from plone import api
from plone.testing import zope

GENERIC_LOGOUT_URL = "/Shibboleth.sso/Logout"
TEST_IDPS = [{"domain": "tester", "name": "tester", "idp_logout": "https://foo.bar/logout"}]


class TestLogin:
    def test_change_password(self, portal):
        view = api.content.get_view(context=portal, name="change-password")
        assert view.__name__ == "change-password"
        view()

    def test_login_url(self, portal):
        view = api.content.get_view(context=portal, name="get_login_url")
        assert view() == "http://nohost/plone/@@login?came_from=http://nohost"

    def test_missing_plugin(self, portal):
        portal.acl_users.manage_delObjects(["ims_sso_plugin"])
        view = api.content.get_view(context=portal, name="get_login_url")
        assert view() == "http://nohost/plone"

    def test_login_condition_yes_plone(self, portal):
        """Plone authenticated"""
        view = api.content.get_view(context=portal, name="login_condition")
        assert view() is False

    def test_login_condition_no_plone_no_shibboleth(self, portal):
        """Plone not authenticated, Shibboleth not authenticated"""
        zope.logout()
        view = api.content.get_view(context=portal, name="login_condition")
        assert view() is True

    def test_login_condition_no_plone_yes_shibboleth(self, portal, http_request, sso):
        """Plone not authenticated, Shibboleth authenticated"""
        http_request.environ[sso.get_setting("shib_header_user")] = "siteadmin"
        http_request.environ[sso.get_setting("shib_header_idp")] = "testdomain"
        http_request[sso.get_setting("shib_header_email")] = "noreply@nohost.com"
        zope.logout()
        view = api.content.get_view(context=portal, name="login_condition")
        assert view() is False

    def test_require_login_yes_plone(self, portal):
        """Plone authenticated"""
        view = api.content.get_view(context=portal, name="require_login")
        assert "You do not have sufficient privileges" in view()

    def test_require_login_no_plone_no_shibboleth(self, portal):
        """Plone not authenticated, Shibboleth not authenticated"""
        zope.logout()
        view = api.content.get_view(context=portal, name="require_login")
        assert "Access Denied" in view()
        assert "Unauthorized" not in view()

    def test_require_login_no_plone_yes_shibboleth(self, portal, http_request, sso):
        """Plone not authenticated, Shibboleth authenticated"""
        http_request.environ[sso.get_setting("shib_header_user")] = "siteadmin"
        http_request.environ[sso.get_setting("shib_header_idp")] = "testdomain"
        http_request[sso.get_setting("shib_header_email")] = "noreply@nohost.com"
        zope.logout()
        view = api.content.get_view(context=portal, name="require_login")
        assert "Access Denied" not in view()
        assert "Unauthorized" in view()

    def test_logout_url(self, http_request, sso, shib_header_user, shib_header_idp):
        api.portal.set_registry_record(
            name="idps",
            interface=ISSOSettings,
            value=TEST_IDPS,
        )
        api.portal.set_registry_record(name="generic_logout", interface=ISSOSettings, value=GENERIC_LOGOUT_URL)
        http_request.environ = {
            shib_header_idp: "tester",
            shib_header_user: "wohnlice",
        }
        logout = sso.get_url_logout(request=http_request)
        assert logout == "https://foo.bar/logout"

        http_request.environ[shib_header_idp] = "https://othersite.com"
        logout = sso.get_url_logout(request=http_request)
        assert logout == GENERIC_LOGOUT_URL
