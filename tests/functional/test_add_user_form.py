import transaction
from ims.sso.interfaces import ISSOSettings
from plone import api


class TestAddUserForm:
    def test_form(self, browser, mock_mail):
        """`mock_mail` is needed to configure the mail host"""
        api.portal.set_registry_record(name="mail_format", interface=ISSOSettings, value="ims.sso.idp.nosso")
        transaction.commit()

        browser.open(f"{api.portal.get().absolute_url()}/new-user")
        ctrl = browser.getControl
        ctrl(name="form.widgets.email").value = "guido@python.org"
        ctrl(name="form.widgets.first_name").value = "Guido"
        ctrl(name="form.widgets.last_name").value = "Van Rossum"
        ctrl(name="form.buttons.register").click()
        assert api.user.get(userid="van-rossum-guido")

    def test_not_configured(self, browser):
        browser.open(f"{api.portal.get().absolute_url()}/new-user")
        assert browser.url.endswith("usergroup-userprefs")
        assert "SSO not properly configured" in browser.contents

    def test_cancel_form(self, browser, mock_mail):
        """`mock_mail` is needed to configure the mail host"""
        api.portal.set_registry_record(name="mail_format", interface=ISSOSettings, value="ims.sso.idp.nosso")
        transaction.commit()

        browser.open(f"{api.portal.get().absolute_url()}/new-user")
        ctrl = browser.getControl
        ctrl(name="form.buttons.cancel").click()
        assert "User registration cancelled" in browser.contents
