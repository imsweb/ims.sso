from plone import api

from ims.users.configs import ACTIVE_STATUS
from ims.users.configs import DISABLED_STATUS

KNOWN_USER_ID = "wohnlice"
KNOWN_USER_LOGIN = "wohnlice@adfs.omni.imsweb.com"
VIEW_NAME = "ldap-update-users"


class TestAutomateUsers:
    def test_from_scratch(self, portal):
        assert api.user.get(KNOWN_USER_ID) is None
        api.content.get_view(VIEW_NAME, context=portal)()
        user = api.user.get(KNOWN_USER_ID)
        assert user.getUserName() == KNOWN_USER_LOGIN

    def test_reactivate(self, portal):
        usr = api.user.create(
            username=KNOWN_USER_ID,
            email="noreply@nohost.com",
            properties={"active": DISABLED_STATUS},
        )
        pas = api.portal.get_tool("acl_users")
        pas.updateLoginName(KNOWN_USER_ID, KNOWN_USER_LOGIN)
        assert usr.getProperty("active") == DISABLED_STATUS

        api.content.get_view(VIEW_NAME, context=portal)()
        usr = api.user.get(
            username=KNOWN_USER_ID
        )  # the old user metadata appears to be stale, perhaps cached per request?
        assert usr.getProperty("active") == ACTIVE_STATUS

    def test_do_deactivate(self, portal, pas):
        usr = api.user.create(
            username="foobar",
            email="noreply@nohost.com",
            properties={"active": ACTIVE_STATUS},
        )
        pas.updateLoginName("foobar", "noone@adfs.omni.imsweb.com")
        assert usr.getProperty("active") == ACTIVE_STATUS

        api.content.get_view(VIEW_NAME, context=portal)()
        usr = api.user.get(username="foobar")
        assert usr.getProperty("active") == DISABLED_STATUS

    def test_dont_deactivate(self, portal, pas):
        usr = api.user.create(
            username=KNOWN_USER_ID,
            email="noreply@nohost.com",
            properties={"active": ACTIVE_STATUS},
        )
        pas = api.portal.get_tool("acl_users")
        pas.updateLoginName(KNOWN_USER_ID, KNOWN_USER_LOGIN)
        assert usr.getProperty("active") == ACTIVE_STATUS

        api.content.get_view(VIEW_NAME, context=portal)()
        usr = api.user.get(username=KNOWN_USER_ID)
        assert usr.getProperty("active") == ACTIVE_STATUS
