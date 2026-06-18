from email import message_from_bytes

import pytest
from ims.sso.configs import ACTIVE_STATUS
from ims.sso.errors import NoSSOMailTemplatesException
from ims.sso.interfaces import IMailTemplates, IMailTemplatesUtility, ISSOSettings
from plone import api
from zope.component import getUtility, provideUtility


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
    def setup_users(self, portal):
        api.user.create(
            username="user",
            email="noreply@nohost.com",
            roles=["Member"],
            properties={"active": ACTIVE_STATUS},
        )

    @pytest.fixture(autouse=True)
    def setup_settings(self, portal):
        singleton = MyIdpMailTemplates()
        provideUtility(singleton, provides=IMailTemplates, name="ims.sso.test_idp")
        api.portal.set_registry_record(name="mail_format", interface=ISSOSettings, value="ims.sso.test_idp")
        api.portal.set_registry_record(
            name="idps",
            interface=ISSOSettings,
            value=[
                {
                    "domain": "foo.bar",
                    "name": "MyIdp",
                    "idp_logout": "https://foo.bar/logout",
                }
            ],
        )
        api.portal.set_registry_record(
            name="generic_logout",
            interface=ISSOSettings,
            value="https://foo_generic.bar/logout",
        )
        api.portal.set_registry_record(
            name="registration_url",
            interface=ISSOSettings,
            value="https://foo.bar/create-account",
        )

    @property
    def utility(self):
        return getUtility(IMailTemplatesUtility)

    def test_registration_url(self, sso):
        reg = sso.get_url_registration()
        assert "foo.bar" in reg

    def test_utility_registered_notify(self):
        assert isinstance(self.utility.get_mailer(), MyIdpMailTemplates)

        msg = self.utility.registered_notify()
        assert "If you do not have a MyIdp account" in msg

    def test_utility_mail_relink(self):
        assert isinstance(self.utility.get_mailer(), MyIdpMailTemplates)

        msg = self.utility.mail_relink()
        assert "If you do not have a MyIdp account" in msg

    def test_default_template_registered_notify(self):
        api.portal.set_registry_record(name="mail_format", interface=ISSOSettings, value="ims.sso.idp.nosso")
        msg = self.utility.registered_notify()
        assert msg

    def test_default_template_mail_relink(self):
        api.portal.set_registry_record(name="mail_format", interface=ISSOSettings, value="ims.sso.idp.nosso")
        msg = self.utility.mail_relink()
        assert msg

    def test_email_registered_notify(self, portal, mock_mail):
        """Test the `registered_notify_template` view and resulting email"""
        userid = "wohnlich-eric"
        assert not api.user.get(username=userid)
        view = api.content.get_view(context=portal, name="new-user")
        view.update()

        data = {
            "email": "wohnlice@imsweb.com",
            "first_name": "Eric",
            "last_name": "Wohnlich",
        }
        view.generate_user_id(data)  # this would be called automatically by the action_join buttonAndHandler
        view.handle_join_success(data)
        assert api.user.get(username=userid)

        msg = message_from_bytes(mock_mail.messages[-1])
        assert "To log in to Plone site, you must use MyIdP" in msg.get_payload()

    def test_email_mail_relink(self, portal, mock_mail, http_request):
        """Test the `mail_password_template` email"""
        reg = api.portal.get_tool("portal_registration")
        reg.mailPassword("user", http_request)

        msg = message_from_bytes(mock_mail.messages[-1])
        assert "Please update your login service for Plone site by linking a MyIdp account" in msg.get_payload()


class TestMisconfigMailers:
    @property
    def utility(self):
        return getUtility(IMailTemplatesUtility)

    def test_no_mailer(self, portal):
        with pytest.raises(NoSSOMailTemplatesException):
            self.utility.get_mailer()
