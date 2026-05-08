import datetime

from plone import api
from zope.annotation.interfaces import IAnnotations
from zope.component import getUtility
from zope.globalrequest import getRequest
from plone.app.testing import TEST_USER_ID
from plone.testing import zope
import pytest
from ims.users.configs import ACTIVE_STATUS
from ims.users.configs import AUTHENTICATED_KEY
from ims.users.configs import INACTIVE_STATUS
from ims.users.interfaces import IReactivationUtility


class TestAutoReactivation:
    @pytest.fixture(autouse=True)
    def setup_users(self, portal):
        # api.env.adopt_roles does not work here so set and unset Manager role to create user
        # with api.env.adopt_roles(["Manager"]):
        old_roles = api.user.get_roles(username=TEST_USER_ID)
        zope.setRoles(portal["acl_users"], TEST_USER_ID, ["Manager"])
        api.user.create(
            username="iadmin",
            email="noreply@nohost.com",
            roles=["Member", "Site Administrator"],
            properties={"active": ACTIVE_STATUS},
        )
        api.user.create(
            username="imanager",
            email="noreply@nohost.com",
            roles=["Member", "Manager"],
            properties={"active": ACTIVE_STATUS},
        )
        zope.setRoles(portal["acl_users"], TEST_USER_ID, old_roles)

    def set_user(self, user_id):
        usr = api.user.get(user_id)

        # simulate logged in user
        request = getRequest()
        annotations = IAnnotations(request)
        annotations[AUTHENTICATED_KEY] = user_id

        return usr

    def test_generate_key(self):
        util = getUtility(IReactivationUtility)
        self.set_user("iadmin")
        assert util.get_activation_key() is None

        _key, _ = util.request_reactivation()
        assert util.get_activation_key()["activation_key"] == _key

    def test_reactivate_user(self):
        util = getUtility(IReactivationUtility)
        usr = self.set_user("iadmin")

        with api.env.adopt_roles(["Manager"]):
            usr.setProperties(active=INACTIVE_STATUS)
            assert usr.getProperty("active") == INACTIVE_STATUS

            _key, _ = util.request_reactivation()
            resp = util.reactivate_user(activation_key=_key)

            # user should be valid and set to active
            util.purge_annotations()  # assert this does NOT remove our valid key
            assert resp is True
            assert api.user.get("iadmin").getProperty("active") == ACTIVE_STATUS

            # key should be deleted
            assert util.get_activation_key() is None

    def test_invalid_reactivation_key(self):
        util = getUtility(IReactivationUtility)
        usr = self.set_user("iadmin")

        with api.env.adopt_roles(["Manager"]):
            usr.setProperties(active=INACTIVE_STATUS)
            assert usr.getProperty("active") == INACTIVE_STATUS

            _key, _ = util.request_reactivation()
            resp = util.reactivate_user(activation_key=_key + "foobar")
            assert resp is False
            assert api.user.get("iadmin").getProperty("active") == INACTIVE_STATUS

    def test_expired_reactivation_key(self, portal):
        util = getUtility(IReactivationUtility)
        usr = self.set_user("iadmin")
        with api.env.adopt_roles(["Manager"]):
            usr.setProperties(active=INACTIVE_STATUS)
            assert usr.getProperty("active") == INACTIVE_STATUS

            # simulate by setting expiry to older date
            _key, _ = util.request_reactivation()
            annotations = IAnnotations(portal)
            annotations[util.annotation_key]["iadmin"]["expiry"] = datetime.datetime.utcnow() - datetime.timedelta(
                days=4
            )

            resp = util.reactivate_user(activation_key=_key + "foobar")
            assert resp is False
            assert api.user.get("iadmin").getProperty("active") == INACTIVE_STATUS

    def test_expired_reactivation_key_purge(self, portal):
        util = getUtility(IReactivationUtility)
        usr = self.set_user("iadmin")
        with api.env.adopt_roles(["Manager"]):
            usr.setProperties(active=INACTIVE_STATUS)
            assert usr.getProperty("active") == INACTIVE_STATUS

            # simulate by setting expiry to older date
            _key, _ = util.request_reactivation()
            annotations = IAnnotations(portal)
            annotations[util.annotation_key]["iadmin"]["expiry"] = datetime.datetime.utcnow() - datetime.timedelta(
                days=4
            )

            util.purge_annotations()
            assert api.user.get("iadmin").getProperty("active") == INACTIVE_STATUS
