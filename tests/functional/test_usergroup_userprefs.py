import datetime

import pytest
from bs4 import BeautifulSoup
from DateTime import DateTime
from ims.sso.configs import ACTIVE_STATUS, DISABLED_STATUS, INACTIVE_STATUS, NOT_LINKED
from ims.sso.interfaces import ISSOSettings
from plone import api
from transaction import commit


class TestUserGroupsPage:
    @property
    def view_url(self):
        return f"{api.portal.get().absolute_url()}/usergroup-userprefs"

    @pytest.fixture
    def setup_users(self, portal, sso):
        api.user.create(
            username="active_user",
            email="active_user@nohost.com",
            roles=["Member"],
            properties={
                "active": ACTIVE_STATUS,
                "first_name": "foo",
                "last_name": "bar",
                "login_time": DateTime(),
                "activation_date": datetime.datetime.now() - datetime.timedelta(4),
            },
        )
        sso.set_login_name("active_user", "active_user@imsweb.com")
        api.user.create(
            username="inactive_user",
            email="inactive_user@nohost.com",
            roles=["Member"],
            properties={"active": INACTIVE_STATUS},
        )
        sso.set_login_name("inactive_user", "inactive_user@imsweb.com")
        api.user.create(
            username="disabled_user",
            email="disabled_user@nohost.com",
            roles=["Member"],
            properties={"active": DISABLED_STATUS},
        )
        sso.set_login_name("disabled_user", "disabled_user@imsweb.com")
        api.user.create(
            username="siteadmin",
            email="siteadmin@nohost.com",
            roles=["Member", "Site Administrator"],
            properties={"active": ACTIVE_STATUS},
        )
        api.user.create(
            username="manager",
            email="manager@nohost.com",
            roles=["Member", "Manager"],
            properties={"active": ACTIVE_STATUS},
        )
        api.user.create(
            username="unlinked", email="unlinked@nohost.com", roles=["Member"], properties={"active": INACTIVE_STATUS}
        )
        sso.set_login_name("unlinked", f"123@{NOT_LINKED}")
        commit()

    def test_search_active_status(self, browser, setup_users):
        browser.open(self.view_url)
        ctrl = browser.getControl

        # active
        ctrl(name="active_status:list", index=0).value = ["active"]
        ctrl(name="form.button.Search").click()
        soup = BeautifulSoup(browser.contents, "html.parser")

        assert len(soup.find_all("input", {"name": "delete:list", "value": "active_user"})) == 1
        assert not soup.find_all("input", {"name": "delete:list", "value": "inactive_user"})
        assert not soup.find_all("input", {"name": "delete:list", "value": "disabled_user"})

        # inactive
        ctrl(name="active_status:list", index=0).value = ["inactive"]
        ctrl(name="form.button.Search").click()
        soup = BeautifulSoup(browser.contents, "html.parser")
        assert not soup.find_all("input", {"name": "delete:list", "value": "active_user"})
        assert len(soup.find_all("input", {"name": "delete:list", "value": "inactive_user"})) == 1
        assert not soup.find_all("input", {"name": "delete:list", "value": "disabled_user"})

        # disabled
        ctrl(name="active_status:list", index=0).value = ["disabled"]
        ctrl(name="form.button.Search").click()
        soup = BeautifulSoup(browser.contents, "html.parser")
        assert not soup.find_all("input", {"name": "delete:list", "value": "active_user"})
        assert not soup.find_all("input", {"name": "delete:list", "value": "inactive_user"})
        assert len(soup.find_all("input", {"name": "delete:list", "value": "disabled_user"})) == 1

    def test_search_find_all(self, browser, setup_users):
        browser.open(self.view_url)
        ctrl = browser.getControl

        # FindAll should ignore these
        ctrl(name="active_status:list", index=0).value = ["active"]
        ctrl(name="form.button.FindAll").click()

        soup = BeautifulSoup(browser.contents, "html.parser")
        assert len(soup.find_all("input", {"name": "delete:list", "value": "active_user"})) == 1
        assert len(soup.find_all("input", {"name": "delete:list", "value": "inactive_user"})) == 1
        assert len(soup.find_all("input", {"name": "delete:list", "value": "disabled_user"})) == 1

    def test_show_expiry_warning(self, browser, sso):
        api.user.create(
            username="active_user",
            email="active_user@nohost.com",
            roles=["Member"],
            properties={"active": INACTIVE_STATUS, "created_date": datetime.date.today()},
        )
        sso.initialize_login("active_user")
        commit()
        browser.open(self.view_url)

        ctrl = browser.getControl
        ctrl(name="form.button.FindAll").click()

        soup = BeautifulSoup(browser.contents, "html.parser")
        for query in soup.find_all("span", attrs={"class": "not-linked"}):
            assert "until removal" in str(query)

    def test_show_expired(self, browser, sso):
        expiry = sso.get_setting("user_account_expiry")
        api.user.create(
            username="active_user",
            email="active_user@nohost.com",
            roles=["Member"],
            properties={
                "active": INACTIVE_STATUS,
                "created_date": datetime.date.today() - datetime.timedelta(expiry + 1),
            },
        )
        sso.initialize_login("active_user")
        commit()
        browser.open(self.view_url)

        ctrl = browser.getControl
        ctrl(name="form.button.FindAll").click()

        soup = BeautifulSoup(browser.contents, "html.parser")
        for query in soup.find_all("span", attrs={"class": "not-linked"}):
            assert "has expired" in str(query)

    def test_show_date_not_set(self, browser, sso):
        api.user.create(
            username="active_user",
            email="active_user@nohost.com",
            roles=["Member"],
            properties={"active": INACTIVE_STATUS},
        )
        sso.initialize_login("active_user")
        commit()
        browser.open(self.view_url)

        ctrl = browser.getControl
        ctrl(name="form.button.FindAll").click()

        soup = BeautifulSoup(browser.contents, "html.parser")
        for query in soup.find_all("span", attrs={"class": "not-linked"}):
            assert "not set" in str(query)

    def test_sort_service_accounts(self, browser):
        """Service accounts are sorted last alphabetically"""
        api.user.create(
            username="api",
            email="noreply@nohost.com",
            roles=["Member"],
            properties={"active": ACTIVE_STATUS, "service": True},
        )
        commit()

        browser.open(self.view_url)
        soup = BeautifulSoup(browser.contents, "html.parser")
        assert len(soup.find_all("td", {"data-sort": "zzapi"})) == 1
        assert not soup.find_all("td", {"data-sort": "api"})

    def test_cant_deactivate_manager(self, browser, setup_users):
        browser.open(self.view_url)
        ctrl = browser.getControl

        # get manager
        soup = BeautifulSoup(browser.contents, "html.parser")
        for idx, el in enumerate(soup.find_all("input", {"name": "users.id:records"})):
            if el.attrs["value"] == "manager":
                assert ctrl(name="users.active:records", index=idx).disabled
            else:
                assert not ctrl(name="users.active:records", index=idx).disabled

    def test_reregister(self, browser, setup_users, mock_mail):
        api.portal.set_registry_record(name="mail_format", interface=ISSOSettings, value="ims.sso.idp.nosso")
        commit()

        browser.open(self.view_url)
        ctrl = browser.getControl

        ctrl(name="users.resetpassword:records", index=0).value = "active_user"
        ctrl(name="users.reset_email:records", index=0).value = "newemail@imsweb.com"
        ctrl(name="form.button.Modify", index=0).click()
        commit()

        assert api.user.get(username="active_user").getProperty("email") == "newemail@imsweb.com"

    def test_reregister_no_mail_format(self, browser, setup_users, mock_mail):
        browser.open(self.view_url)
        ctrl = browser.getControl

        ctrl(name="users.resetpassword:records", index=0).value = "active_user"
        ctrl(name="users.reset_email:records", index=0).value = "newemail@imsweb.com"
        ctrl(name="form.button.Modify", index=0).click()
        commit()
        assert "Request was not sent" in browser.contents

    def test_reregister_invalid_email(self, browser, setup_users):
        browser.open(self.view_url)
        ctrl = browser.getControl

        ctrl(name="users.resetpassword:records", index=0).value = "active_user"
        ctrl(name="users.reset_email:records", index=0).value = "newemail"
        ctrl(name="form.button.Modify", index=0).click()
        commit()

        assert api.user.get(username="active_user").getProperty("email") == "active_user@nohost.com"

    def test_searchstring_user(self, browser, setup_users):
        browser.open(self.view_url)
        ctrl = browser.getControl

        soup = BeautifulSoup(browser.contents, "html.parser")
        active_users = [usr for usr in api.user.get_users() if usr.getProperty("active") == ACTIVE_STATUS]
        assert len(soup.select("#users_manage_table tbody tr")) == len(active_users)

        ctrl(name="searchstring", index=0).value = "siteadmin"
        ctrl(name="form.button.Search").click()

        soup = BeautifulSoup(browser.contents, "html.parser")
        assert len(soup.select("#users_manage_table tbody tr")) == 1

        ctrl(name="searchstring", index=0).value = "foo bar"
        ctrl(name="form.button.Search").click()
        assert len(soup.select("#users_manage_table tbody tr")) == 1

    def test_delete_user(self, browser, setup_users):
        browser.open(self.view_url)
        ctrl = browser.getControl

        ctrl(name="delete:list", index=0).value = "active_user"
        ctrl(name="form.button.Modify", index=0).click()
        commit()

        assert not api.user.get(username="active_user")

    def test_handle_missing_login_time(self, browser, setup_users):
        usr = api.user.get(username="active_user")
        usr.setMemberProperties({"login_time": None})

        browser.open(self.view_url)
        ctrl = browser.getControl

        # FindAll should ignore these
        ctrl(name="form.button.FindAll").click()
        soup = BeautifulSoup(browser.contents, "html.parser")
        assert len(soup.select("#users_manage_table tbody tr")) == len(api.user.get_users())

    def test_change_status(self, browser, setup_users):
        browser.open(self.view_url)
        ctrl = browser.getControl

        ctrl(name="searchstring", index=0).value = "active_user"
        ctrl(name="active_status:list", index=0).value = ["active", "disabled"]
        ctrl(name="form.button.Search").click()

        ctrl(name="users.active:records").value = ["disabled"]
        ctrl(name="form.button.Modify", index=0).click()
        commit()

        assert api.user.get(username="active_user").getProperty("active") == DISABLED_STATUS

        ctrl(name="users.active:records").value = ["active"]
        ctrl(name="form.button.Modify", index=0).click()
        commit()

        assert api.user.get(username="active_user").getProperty("active") == ACTIVE_STATUS

    def test_delete_users_from_groups(self, browser, setup_users):
        """In lieue of knowing how to test this properly, at least make sure it doesn't error"""
        api.group.create(groupname="foo", title="Foo")
        api.group.add_user(groupname="foo", username="active_user")
        commit()
        browser.open(self.view_url)
        ctrl = browser.getControl

        ctrl(name="searchstring", index=0).value = "active_user"
        ctrl(name="form.button.Search").click()

        ctrl(name="delete:list").value = "active_user"
        ctrl(name="form.button.Modify", index=0).click()
        commit()

        assert not api.user.get(username="active_user")
