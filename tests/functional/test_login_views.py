from plone import api
from Products.Sessions import install_browser_id_manager
from transaction import commit

from ims.sso.interfaces import ISSOSettings


class TestLogin:
    def test_login_page(self, portal, browser):
        browser.open(f"{portal.absolute_url()}/login")
        assert browser.contents

    def test_logout(self, app, portal, browser):
        api.portal.set_registry_record(name="generic_logout", interface=ISSOSettings, value=portal.absolute_url())
        install_browser_id_manager(app)
        commit()

        logout_url = f"{portal.absolute_url()}/logout"

        browser.open(portal.absolute_url())
        # set fake cookie to ensure its expired
        browser.cookies["foo"] = {
            "value": "foobar",
            "path": "/",
            "expires": "Thu, 01 Jan 2070 00:00:00 GMT",
        }
        assert len(browser.cookies) == 1

        browser.open(logout_url)
        assert browser.url == api.portal.get().absolute_url()
        assert len(browser.cookies) == 0

    def change_password(self, browser):
        """should redirect back to home"""
        browser.open(f"{api.portal.get().absolute_url()}/change-password")
        assert "This site uses single sign-on to authenticate users" in browser.content

    def test_single_idp(self, browser, fake_idp_login):
        login_url = f"{api.portal.get().absolute_url()}/login"
        api.portal.set_registry_record(interface=ISSOSettings, name="primary_idps", value=["foologin.bar"])
        api.portal.set_registry_record(interface=ISSOSettings, name="always_show_login", value=True)
        commit()

        browser.open(login_url)
        assert browser.url == login_url

        api.portal.set_registry_record(interface=ISSOSettings, name="always_show_login", value=False)
        commit()

        browser.open(login_url)
        assert browser.url != login_url
