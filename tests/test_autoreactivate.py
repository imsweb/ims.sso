import datetime
from email import message_from_bytes

import pytest
from ims.sso.configs import ACTIVE_STATUS, AUTHENTICATED_KEY, INACTIVE_STATUS
from ims.sso.interfaces import IReactivationUtility
from plone import api
from plone.protect.authenticator import createToken
from plone.testing import zope
from Products.statusmessages.interfaces import IStatusMessage
from zope.annotation.interfaces import IAnnotations
from zope.component import getUtility


class TestAutoReactivation:
    @pytest.fixture(autouse=True)
    def setup_users(self, portal):
        api.user.create(
            username="user",
            email="noreply@nohost.com",
            roles=["Member"],
            properties={"active": ACTIVE_STATUS},
        )
        api.user.create(
            username="siteadmin",
            email="noreply@nohost.com",
            roles=["Member", "Site Administrator"],
            properties={"active": ACTIVE_STATUS},
        )
        api.user.create(
            username="manager",
            email="noreply@nohost.com",
            roles=["Member", "Manager"],
            properties={"active": ACTIVE_STATUS},
        )

    def set_user(self, user_id, request, sso):
        usr = api.user.get(user_id)

        # configure Shiboboleth headers
        annotations = IAnnotations(request)
        annotations[AUTHENTICATED_KEY] = user_id
        request.environ[sso.get_setting("shib_header_user")] = "siteadmin"
        request.environ[sso.get_setting("shib_header_idp")] = "testdomain"
        request[sso.get_setting("shib_header_email")] = "noreply@nohost.com"

        # we configure the headers, but are logged out of Plone
        zope.logout()

        return usr

    def get_status_message(self, view):
        """Fetch status message directly"""
        sm = IStatusMessage(view.request)
        return sm.show()[-1].message

    def test_generate_key(self, http_request, sso):
        util = getUtility(IReactivationUtility)
        self.set_user("siteadmin", http_request, sso)
        assert util.get_activation_key() is None

        _key, _ = util.request_reactivation()
        assert util.get_activation_key()["activation_key"] == _key

    def test_reactivate_user(self, http_request, sso):
        util = getUtility(IReactivationUtility)
        usr = self.set_user("siteadmin", http_request, sso)

        with api.env.adopt_roles(["Manager"]):
            usr.setProperties(active=INACTIVE_STATUS)
        assert usr.getProperty("active") == INACTIVE_STATUS

        _key, _ = util.request_reactivation()
        resp = util.reactivate_user(activation_key=_key)

        # user should be valid and set to active
        util.purge_activation_keys()  # assert this does NOT remove our valid key
        assert resp is True
        assert api.user.get("siteadmin").getProperty("active") == ACTIVE_STATUS

        # key should be deleted
        assert util.get_activation_key() is None

    def test_browser_request_email(self, portal, mock_mail, http_request, sso):
        # same as above but through browser.login.ReactivateUserAccount
        self.set_user("user", http_request, sso)

        mock_mail.reset()

        view = api.content.get_view(context=portal, name="request_reactivation")
        view.request.environ["HTTP_X_CSRF_TOKEN"] = createToken()
        view.request["REQUEST_METHOD"] = "POST"
        view.render()

        msg = message_from_bytes(mock_mail.messages[0])
        assert "To reactivate your account" in msg.get_payload()

    def test_browser_invalid_request_key(self, portal, http_request, sso):
        # only way for this to happen is no user id in header/annotations
        view = api.content.get_view(context=portal, name="request_reactivation")
        view.request.environ["HTTP_X_CSRF_TOKEN"] = createToken()
        view.request["REQUEST_METHOD"] = "POST"
        view()
        assert "An activation key could not be obtained," in self.get_status_message(view)

    def test_invalid_reactivation_key(self, http_request, sso):
        util = getUtility(IReactivationUtility)
        usr = self.set_user("siteadmin", http_request, sso)

        with api.env.adopt_roles(["Manager"]):
            usr.setProperties(active=INACTIVE_STATUS)
        assert usr.getProperty("active") == INACTIVE_STATUS

        _key, _ = util.request_reactivation()
        resp = util.reactivate_user(activation_key=_key + "foobar")
        assert resp is False
        assert api.user.get("siteadmin").getProperty("active") == INACTIVE_STATUS

    def test_browser_invalid_reactivation_key(self, portal, http_request, sso):
        util = getUtility(IReactivationUtility)
        usr = self.set_user("siteadmin", http_request, sso)

        with api.env.adopt_roles(["Manager"]):
            usr.setProperties(active=INACTIVE_STATUS)
        assert usr.getProperty("active") == INACTIVE_STATUS

        _key, _ = util.request_reactivation()

        # no key
        view = portal.restrictedTraverse("reactivate_user")
        view()
        assert "invalid request" in self.get_status_message(view)
        assert api.user.get("siteadmin").getProperty("active") == INACTIVE_STATUS

        # bad key
        view = portal.restrictedTraverse("reactivate_user")
        view.publishTraverse(view.request, _key + "foobar")
        view()
        assert "Your account could not be activated" in self.get_status_message(view)
        assert api.user.get("siteadmin").getProperty("active") == INACTIVE_STATUS

        # good key
        view = portal.restrictedTraverse("reactivate_user")
        view.publishTraverse(view.request, _key)
        view()
        assert api.user.get("siteadmin").getProperty("active") == ACTIVE_STATUS
        assert "success" in self.get_status_message(view)

    def test_expired_reactivation_key(self, portal, http_request, sso):
        util = getUtility(IReactivationUtility)
        usr = self.set_user("siteadmin", http_request, sso)
        with api.env.adopt_roles(["Manager"]):
            usr.setProperties(active=INACTIVE_STATUS)
        assert usr.getProperty("active") == INACTIVE_STATUS

        # simulate by setting expiry to older date
        _key, _date = util.request_reactivation()
        annotations = IAnnotations(portal)
        annotations[util.annotation_key]["siteadmin"]["expiry"] = datetime.datetime.now() - datetime.timedelta(days=4)

        resp = util.reactivate_user(activation_key=_key)
        assert resp is False
        assert api.user.get("siteadmin").getProperty("active") == INACTIVE_STATUS

    def test_expired_reactivation_key_purge(self, portal, http_request, sso):
        util = getUtility(IReactivationUtility)
        usr = self.set_user("siteadmin", http_request, sso)
        with api.env.adopt_roles(["Manager"]):
            usr.setProperties(active=INACTIVE_STATUS)
        assert usr.getProperty("active") == INACTIVE_STATUS

        # simulate by setting expiry to older date
        util.request_reactivation()
        annotations = IAnnotations(portal)
        annotations[util.annotation_key]["siteadmin"]["expiry"] = datetime.datetime.now() - datetime.timedelta(days=4)

        util.purge_activation_keys()
        assert api.user.get("siteadmin").getProperty("active") == INACTIVE_STATUS

    # def test_request_reactivation_view(self):
    #     # browser.login.RequestReactivation
    #     raise NotImplementedError
