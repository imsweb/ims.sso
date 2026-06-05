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

        browser.open(f"{api.portal.get().absolute_url()}/sso-logout")
        assert browser.url == api.portal.get().absolute_url()

    def change_password(self, browser):
        """should redirect back to home"""
        browser.open(f"{api.portal.get().absolute_url()}/change-password")
        assert "This site uses single sign-on to authenticate users" in browser.content
