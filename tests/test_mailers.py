import pytest
from ims.sso.configs import CHALLENGE_HEADER_KEY, IDP_KEY
from ims.sso.interfaces import IMailTemplatesUtility
from ims.sso.utility import (
    ADFS_LOGOUT_URL,
    GENERIC_LOGOUT_URL,
    LINK_ACCOUNT,
    LOGOUT,
    OKTA_LOGOUT_URL,
    REGISTRATION,
)
from plone import api
from zope.component import getUtility


class TestPlugins:
    @pytest.fixture(autouse=True)
    def setup_users(self, sso):
        self.email_params = {
            "link_url": sso.get_url(LINK_ACCOUNT, randomstring="froggy", userid="foobar"),
            "registration_email": sso.get_url(REGISTRATION, email="noreplay@imsweb.com"),
            "okta_registration_url": sso.get_url(REGISTRATION, email="noreplay@imsweb.com", okta=True),
            "logingov_registration_url": sso.get_url(REGISTRATION, email="noreplay@imsweb.com"),
            "portal_title": "Super site!",
            "to_name": "wohnlice@imsweb.com",
            "from_name": "wohnlice@imsweb.com",
            "subject": "mail",
            "timeout": "",
            "timeout_d": "",
        }

    def test_registration_url(self, sso):
        reg = sso.get_url(REGISTRATION, email="noreply@imsweb.com")
        assert "login.gov" in reg

    def test_registration_url_required_params(self, sso):
        with pytest.raises(TypeError):
            sso.get_url(REGISTRATION)

    def test_logout_url(self, http_request, sso):
        http_request.environ = {
            IDP_KEY: "https://adfs.omni.imsweb.com/loginfoobar",
            CHALLENGE_HEADER_KEY: "wohnlice",
        }
        logout = sso.get_url(LOGOUT, request=http_request)
        assert logout == f"/Shibboleth.sso/Logout?return={ADFS_LOGOUT_URL}"
        http_request.environ[IDP_KEY] = "https://www.okta.com/ims"
        logout = sso.get_url(LOGOUT, request=http_request)
        assert logout == f"/Shibboleth.sso/Logout?return={OKTA_LOGOUT_URL}"
        http_request.environ[IDP_KEY] = "https://foobar.com"
        logout = sso.get_url(LOGOUT, request=http_request)
        assert logout == f"/Shibboleth.sso/Logout?return={GENERIC_LOGOUT_URL}"

    def test_logout_url_required_params(self, sso):
        with pytest.raises(TypeError):
            sso.get_url(LOGOUT)

    def test_relink_url(self, sso):
        relink = sso.get_url(LINK_ACCOUNT, randomstring="froggy", userid="wohnlice")
        assert "/linkaccount/froggy/wohnlice" in relink

    def test_relink_url_required_params(self, sso):
        with pytest.raises(TypeError):
            sso.get_url(LINK_ACCOUNT)
        with pytest.raises(TypeError):
            sso.get_url(LINK_ACCOUNT, randomstring="froggy")
        with pytest.raises(TypeError):
            sso.get_url(LINK_ACCOUNT, userid="wohnlice")

    def test_password_reset_mailer_ims_nih(self, portal):
        templater = getUtility(IMailTemplatesUtility)
        api.portal.set_registry_record("ims.users.interfaces.IControlPanel.mail_format", "ims.users.idp.ims_nih")
        password_form = templater.mail_password().format(**self.email_params)
        registration_form = templater.registered_notify().format(**self.email_params)
        assert "IMS Login Service" in password_form
        assert "NIH Network" in password_form
        assert "IMS Login Service" in registration_form
        assert "NIH Network" in registration_form
        full_form = templater.mail_form(templater.mail_password(), params=self.email_params)
        assert full_form is not None

    def test_password_reset_mailer_ims(self, portal):
        templater = getUtility(IMailTemplatesUtility)
        api.portal.set_registry_record("ims.users.interfaces.IControlPanel.mail_format", "ims.users.idp.ims")
        password_form = templater.mail_password().format(**self.email_params)
        registration_form = templater.registered_notify().format(**self.email_params)
        assert "IMS Login Service" in password_form
        assert "NIH Network" not in password_form
        assert "IMS Login Service" in registration_form
        assert "NIH Network" not in registration_form
        full_form = templater.mail_form(templater.mail_password(), params=self.email_params)
        assert full_form is not None

    def test_password_reset_mailer_nih(self, portal):
        templater = getUtility(IMailTemplatesUtility)
        api.portal.set_registry_record("ims.users.interfaces.IControlPanel.mail_format", "ims.users.idp.nih")
        password_form = templater.mail_password().format(**self.email_params)
        registration_form = templater.registered_notify().format(**self.email_params)
        assert "IMS Login Service" not in password_form
        assert "NIH Network" in password_form
        assert "IMS Login Service" not in registration_form
        assert "NIH Network" in registration_form
        full_form = templater.mail_form(templater.mail_password(), params=self.email_params)
        assert full_form is not None

    def test_password_reset_mailer_ctep(self, portal):
        templater = getUtility(IMailTemplatesUtility)
        api.portal.set_registry_record("ims.users.interfaces.IControlPanel.mail_format", "ims.users.idp.ctep")
        password_form = templater.mail_password().format(**self.email_params)
        registration_form = templater.registered_notify().format(**self.email_params)
        assert "IMS Login Service" not in password_form
        assert "NIH Network" not in password_form
        assert "CTEP" in password_form
        assert "IMS Login Service" not in registration_form
        assert "NIH Network" not in registration_form
        assert "CTEP" in registration_form
        full_form = templater.mail_form(templater.mail_password(), params=self.email_params)
        assert full_form is not None
