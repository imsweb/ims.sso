import pytest
from plone import api
from plone.protect.authenticator import createToken
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
        api.user.create(
            username="siteadmin",
            email="noreply@nohost.com",
            roles=["Member", "Site Administrator"],
            properties={"active": "active"},
        )
        api.user.create(
            username="manager",
            email="noreply@nohost.com",
            roles=["Member", "Manager"],
            properties={"active": "active"},
        )
        # os.environ["PLONE_CSRF_DISABLED"] = "true"

    def test_deactivate(self, portal):
        view = api.content.get_view("usergroup-userprefs", context=portal)
        view.request.environ["HTTP_X_CSRF_TOKEN"] = createToken()
        view.request.method = "POST"
        rec = RequestRecord(id="siteadmin", reset_email="noreply@nohost.com", active="inactive")
        view.manageUser(users=(rec,))
        assert api.user.get("siteadmin").getProperty("active") == "inactive"

    def test_cant_deactivate_manager(self, portal):
        """User cannot deactivate someone with the Manager role"""
        view = api.content.get_view("usergroup-userprefs", context=portal)
        view.request.environ["HTTP_X_CSRF_TOKEN"] = createToken()
        view.request.method = "POST"
        rec = RequestRecord(id="manager", reset_email="noreply@nohost.com", active="active")
        view.manageUser(users=(rec,))
        assert api.user.get("manager").getProperty("active") == "active"

    def test_cant_deactivate_without_permission(self, portal):
        """User must have permission to deactivate/reactivate"""
        with api.env.adopt_user("siteadmin"):
            portal.manage_permission("ims.sso: deactivate", roles=["Manager"])
            view = api.content.get_view("usergroup-userprefs", context=portal)
            view.request.environ["HTTP_X_CSRF_TOKEN"] = createToken()
            view.request.method = "POST"
            rec = RequestRecord(id="siteadmin", reset_email="noreply@nohost.com", active="inactive")
            view.manageUser(users=(rec,))
            assert api.user.get("siteadmin").getProperty("active") == "active"

            portal.manage_permission("ims.sso: deactivate", roles=["Manager", "Site Administrator"])
            view = api.content.get_view("usergroup-userprefs", context=portal)
            view.request.environ["HTTP_X_CSRF_TOKEN"] = createToken()
            view.request.method = "POST"
            rec = RequestRecord(id="siteadmin", reset_email="noreply@nohost.com", active="inactive")
            view.manageUser(users=(rec,))
            assert api.user.get("siteadmin").getProperty("active") == "inactive"
