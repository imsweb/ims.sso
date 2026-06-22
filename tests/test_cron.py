import datetime

import pytest
from ims.sso.configs import NOT_LINKED
from persistent.mapping import PersistentMapping
from plone import api
from zope.annotation.interfaces import IAnnotations


class TestCron:
    @pytest.fixture
    def view(self, portal):
        return api.content.get_view(context=portal, name="sso-tasks")

    @pytest.fixture(autouse=True)
    def setup_users(self, portal, sso):
        self.inactive_days = sso.get_setting("days_until_inactive")
        self.disabled_days = sso.get_setting("days_until_disabled")
        self.user1 = api.user.create(
            username="user1",
            email="noreply@imsweb.com",
            properties={"active": "active", "created_date": datetime.date(2000, 1, 1)},
        )
        self.user2 = api.user.create(
            username="user2",
            email="noreply@imsweb.com",
            properties={"active": "active", "created_date": datetime.date.today()},
        )
        sso.set_login_name(user_id=self.user1.getId(), login_name=f"x@{NOT_LINKED}")
        sso.set_login_name(user_id=self.user2.getId(), login_name=f"y@{NOT_LINKED}")

    def test_browser(self, view):
        content = view()
        assert content == "User accounts updated."

    def test_purge_unlinked(self, view):
        view()

        assert api.user.get("user1") is None
        assert api.user.get("user2") is not None

    def test_disable_user_accounts(self, sso, view):
        self.user1.setMemberProperties({"activation_date": datetime.date.today()})
        sso.set_login_name(self.user1.getId(), "x@plone.org")
        sso.set_login_name(self.user2.getId(), "y@plone.org")
        view()

        # control
        assert api.user.get("user1").getProperty("active") == "active"

        # inactive/disable
        self.user1.setMemberProperties({
            "activation_date": datetime.date.today() - datetime.timedelta(self.inactive_days + 1)
        })
        self.user2.setMemberProperties({
            "activation_date": datetime.date.today() - datetime.timedelta(self.disabled_days + 1)
        })
        view()
        assert api.user.get("user1").getProperty("active") == "inactive"
        assert api.user.get("user2").getProperty("active") == "disabled"

    def test_purge_activation_keys(self, portal, view):
        annotations = IAnnotations(portal)
        activation_key = "_test_key"

        yesterday = datetime.datetime.now() - datetime.timedelta(1)
        tomorrow = datetime.datetime.now() + datetime.timedelta(1)

        annotations["ReactivationUtility"] = PersistentMapping()
        annotations["ReactivationUtility"][self.user1.getId()] = {
            "activation_key": activation_key,
            "expiry": tomorrow,
        }

        # control
        assert len(annotations["ReactivationUtility"]) == 1

        # test active key NOT removed
        view()
        assert len(annotations["ReactivationUtility"]) == 1

        # test expired key IS removed
        annotations["ReactivationUtility"][self.user1.getId()]["expiry"] = yesterday
        view()
        assert len(annotations["ReactivationUtility"]) == 0
