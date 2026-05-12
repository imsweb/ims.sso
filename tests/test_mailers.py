import pytest
from ims.sso.interfaces import IMailTemplates, ISettings
from plone import api
from zope.component import provideUtility


class MyIdpMailTemplates:
    """Only the IMS service provider is available"""

    title = "MyIdp"

    def registered_notify(self):
        return """You ({to_name}) have been registered as a user on {portal_title}.

To log in to {portal_title}, you must use MyIdP.

Step 1: If you do not have a MyIdp account, please create one at https://foo.bar/create-an-account/.
If you already have a MyIdp account, continue to Step 2.

Step 2: Link your MyIdp account with {portal_title} by following this link: {link_url}
"""

    def mail_relink(self):
        return """Please update your login service for {portal_title} by linking a MyIdp account.

Step 1: If you do not have a MyIdp account, please create one at {registration_url}.
If you already have a MyIdp account, continue to Step 2.

Step 2: Link your MyIdp account with {portal_title} by following this link: {link_url}
"""


class TestMailers:
    @pytest.fixture(autouse=True)
    def setup_users(self, sso):
        self.email_params = {
            "link_url": sso.get_url_linkaccount(link_key="froggy", userid="foobar"),
            "registration_email": sso.get_url_registration(),
            "portal_title": "Super site!",
            "to_name": "wohnlice@imsweb.com",
            "from_name": "wohnlice@imsweb.com",
            "subject": "mail",
            "timeout": "",
            "timeout_d": "",
        }

    @pytest.fixture(autouse=True)
    def setup_settings(self, portal):
        provideUtility(MyIdpMailTemplates, provides=IMailTemplates, name="ims.sso.test_idp")
        api.portal.set_registry_record(name="mail_format", interface=ISettings, value="ims.sso.test_idp")
        api.portal.set_registry_record(name="idps", interface=ISettings, value=["foo.bar|MyIdp|https://foo.bar/logout"])
        api.portal.set_registry_record(
            name="generic_logout", interface=ISettings, value="https://foo_generic.bar/logout"
        )
        api.portal.set_registry_record(
            name="registration_url", interface=ISettings, value="https://foo.bar/create-account"
        )

    def test_registration_url(self, sso):
        reg = sso.get_url_registration()
        assert "foo.bar" in reg

    def test_logout_url(self, http_request, sso, shib_header_user, shib_header_idp):
        http_request.environ = {
            shib_header_idp: "https://foo.bar/login",
            shib_header_user: "wohnlice",
        }
        logout = sso.get_url_logout(request=http_request)
        assert logout == "https://foo.bar/logout"

        http_request.environ[shib_header_idp] = "https://othersite.com"
        logout = sso.get_url_logout(request=http_request)
        assert logout == "https://foo_generic.bar/logout"
