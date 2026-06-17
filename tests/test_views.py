import pytest
from ims.sso.browser.viewlets import SsoWarningsViewlet
from ims.sso.configs import ACTIVE_STATUS, AUTHENTICATED_KEY, DISABLED_STATUS, INACTIVE_STATUS
from ims.sso.interfaces import ISSOSettings
from plone import api
from plone.protect.authenticator import createToken
from plone.testing import zope
from zExceptions import Forbidden
from zope.annotation.interfaces import IAnnotations


class TestViews:
    username = "siteadmin"
    email = "noreply@nohost.com"
    idp = "testdomain"
    user = None

    @pytest.fixture(autouse=True)
    def setup_users(self, http_request, sso):
        self.user = api.user.create(
            username=self.username,
            email=self.email,
            roles=["Member", "Site Administrator"],
            properties={"active": ACTIVE_STATUS},
        )
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
        viewlet = SsoWarningsViewlet(portal, http_request, view)
        assert viewlet.is_inactive()
        content = view()
        assert "Your account has been locked due to inactivity" in content

    def test_viewlet_disabled(self, portal, http_request):
        annotations = IAnnotations(http_request)
        annotations[AUTHENTICATED_KEY] = self.username
        zope.logout()
        self.user.setMemberProperties({"active": DISABLED_STATUS})

        view = api.content.get_view(context=portal, name="view")
        viewlet = SsoWarningsViewlet(portal, http_request, view)
        assert viewlet.is_disabled()
        content = view()
        assert "Your account has been disabled" in content

    def test_viewlet_ignored_views(self, portal, http_request):
        annotations = IAnnotations(http_request)
        annotations[AUTHENTICATED_KEY] = self.username
        zope.logout()
        self.user.setMemberProperties({"active": DISABLED_STATUS})

        view = api.content.get_view(context=portal, name="contact-info")
        viewlet = SsoWarningsViewlet(portal, http_request, view)
        assert not viewlet.show_alert()

        api.portal.set_registry_record(interface=ISSOSettings, name="unauth_ignored_views", value=[])
        view = api.content.get_view(context=portal, name="contact-info")
        viewlet = SsoWarningsViewlet(portal, http_request, view)
        assert viewlet.show_alert()

    def test_prevent_remove_manager(self, portal):
        """This case only happens when a non-Manager can change roles. They are still not allowed to remove
        that role
        """
        view = api.content.get_view(context=portal, name="usergroup-userprefs")

        api.user.create(
            username="manager",
            email="manager@nohost.com",
            roles=["Member", "Manager"],
            properties={"active": ACTIVE_STATUS},
        )
        # adopt_user by username doesn't work when login_name is changed
        with api.env.adopt_user(user=api.user.get(username="siteadmin")):
            data = [{"active": "active", "id": "manager", "reset_email": "manager@nohost.com", "roles": ["Member"]}]
            view.request.environ["HTTP_X_CSRF_TOKEN"] = createToken()
            view.request.method = "POST"

            # it will simply ignore this command because they don't have permission
            view.manageUser(users=data)
            assert "Manager" in api.user.get_roles(username="manager")

        # assign permission and run as siteadmin again
        portal.manage_permission("ims.sso: can change roles", roles=["Manager", "Site Administrator"])
        with api.env.adopt_user(user=api.user.get(username="siteadmin")):
            data = [{"active": "active", "id": "manager", "reset_email": "manager@nohost.com", "roles": ["Member"]}]
            view.request.environ["HTTP_X_CSRF_TOKEN"] = createToken()
            view.request.method = "POST"

            with pytest.raises(Forbidden):
                view.manageUser(users=data)
