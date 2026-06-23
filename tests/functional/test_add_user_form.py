from ims.sso.interfaces import ISSOSettings
from plone import api
from transaction import commit


class TestAddUserForm:
    def test_form(self, browser, mock_mail):
        """`mock_mail` is needed to configure the mail host"""
        api.portal.set_registry_record(name="mail_format", interface=ISSOSettings, value="ims.sso.idp.nosso")
        api.group.create(groupname="Editors", title="Editors")
        commit()

        browser.open(f"{api.portal.get().absolute_url()}/new-user")
        ctrl = browser.getControl
        ctrl(name="form.widgets.email").value = "guido@python.org"
        ctrl(name="form.widgets.first_name").value = "Guido"
        ctrl(name="form.widgets.last_name").value = "Van Rossum"
        ctrl(name="form.widgets.groups:list").value = ["Editors"]
        ctrl(name="form.buttons.register").click()
        assert api.user.get(userid="van-rossum-guido")

    def test_form_request_vars(self, browser, mock_mail):
        api.portal.set_registry_record(name="mail_format", interface=ISSOSettings, value="ims.sso.idp.nosso")
        commit()

        browser.open(
            f"{api.portal.get().absolute_url()}/new-user?first_name=Eric&last_name=Wohnlich&email=wohnliche@imsweb.com"
        )
        ctrl = browser.getControl
        assert ctrl(name="form.widgets.email").value == "wohnliche@imsweb.com"
        assert ctrl(name="form.widgets.first_name").value == "Eric"
        assert ctrl(name="form.widgets.last_name").value == "Wohnlich"

    def test_form_dup_confirmation(self, browser, mock_mail):
        """`mock_mail` is needed to configure the mail host"""
        api.portal.set_registry_record(name="mail_format", interface=ISSOSettings, value="ims.sso.idp.nosso")
        api.user.create(username="foo", email="guido@python.org")
        commit()

        browser.open(f"{api.portal.get().absolute_url()}/new-user")
        ctrl = browser.getControl
        ctrl(name="form.widgets.email").value = "guido@python.org"
        ctrl(name="form.widgets.first_name").value = "Guido"
        ctrl(name="form.widgets.last_name").value = "Van Rossum"
        ctrl(name="form.buttons.register").click()
        assert not api.user.get(userid="van-rossum-guido")

        ctrl(name="form.widgets.allow_match").value = "1"
        ctrl(name="form.buttons.register").click()
        assert api.user.get(userid="van-rossum-guido")

    def test_not_configured(self, browser):
        browser.open(f"{api.portal.get().absolute_url()}/new-user")
        assert browser.url.endswith("usergroup-userprefs")
        assert "SSO not properly configured" in browser.contents

    def test_cancel_form(self, browser, mock_mail):
        """`mock_mail` is needed to configure the mail host"""
        api.portal.set_registry_record(name="mail_format", interface=ISSOSettings, value="ims.sso.idp.nosso")
        commit()

        browser.open(f"{api.portal.get().absolute_url()}/new-user")
        ctrl = browser.getControl
        ctrl(name="form.buttons.cancel").click()
        assert "User registration cancelled" in browser.contents
