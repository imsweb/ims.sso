import os

import pytest
from plone import api
from plone.app.testing import TEST_USER_ID
from plone.protect.authenticator import createToken
from plone.testing import zope
from ZPublisher.HTTPRequest import record


class RequestRecord(record):
    """convenience init"""

    def __init__(self, **kwargs):
        super().__init__()
        for k, v in kwargs.items():
            setattr(self, k, v)


class TestActivation:
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
            properties={"active": "active"},
        )
        api.user.create(
            username="imanager",
            email="noreply@nohost.com",
            roles=["Member", "Manager"],
            properties={"active": "active"},
        )
        os.environ["PLONE_CSRF_DISABLED"] = "true"
        zope.setRoles(portal["acl_users"], TEST_USER_ID, old_roles)

    def test_deactivate(self, portal):
        with api.env.adopt_user("imanager"):
            view = api.content.get_view("usergroup-userprefs", context=portal)
            view.request.environ["HTTP_X_CSRF_TOKEN"] = createToken()
            view.request.method = "POST"
            rec = RequestRecord(id="iadmin", reset_email="noreply@nohost.com", active="inactive")
            view.manageUser(users=(rec,))
        assert api.user.get("iadmin").getProperty("active") == "inactive"

    def test_cant_deactivate_manager(self, portal):
        """User cannot deactivate someone with the Manager role"""
        with api.env.adopt_user("iadmin"):
            view = api.content.get_view("usergroup-userprefs", context=portal)
            view.request.environ["HTTP_X_CSRF_TOKEN"] = createToken()
            view.request.method = "POST"
            rec = RequestRecord(id="imanager", reset_email="noreply@nohost.com", active="active")
            view.manageUser(users=(rec,))
        assert api.user.get("imanager").getProperty("active") == "active"

    def test_cant_deactivate_without_permission(self, portal):
        """User must have permission to deactivate/reactivate"""
        with api.env.adopt_user("iadmin"):
            portal.manage_permission("ims.sso: deactivate", roles=["Manager"])
            view = api.content.get_view("usergroup-userprefs", context=portal)
            view.request.environ["HTTP_X_CSRF_TOKEN"] = createToken()
            view.request.method = "POST"
            rec = RequestRecord(id="iadmin", reset_email="noreply@nohost.com", active="inactive")
            view.manageUser(users=(rec,))
            assert api.user.get("iadmin").getProperty("active") == "active"

            portal.manage_permission("ims.sso: deactivate", roles=["Manager", "Site Administrator"])
            view = api.content.get_view("usergroup-userprefs", context=portal)
            view.request.environ["HTTP_X_CSRF_TOKEN"] = createToken()
            view.request.method = "POST"
            rec = RequestRecord(id="iadmin", reset_email="noreply@nohost.com", active="inactive")
            view.manageUser(users=(rec,))
            assert api.user.get("iadmin").getProperty("active") == "inactive"
