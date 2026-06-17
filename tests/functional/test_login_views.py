from ims.sso.interfaces import ISSOSettings
from plone import api
from Products.Sessions import install_browser_id_manager
from transaction import commit


class TestLogin:
    def test_login_page(self, browser):
        """should redirect back to home"""
        browser.open(f"{api.portal.get().absolute_url()}/login")
        assert browser.url == api.portal.get().absolute_url()

    def test_logout(self, app, portal, browser):
        api.portal.set_registry_record(name="generic_logout", interface=ISSOSettings, value=portal.absolute_url())
        install_browser_id_manager(app)
        commit()

        logout_url = f"{api.portal.get().absolute_url()}/sso-logout"

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
