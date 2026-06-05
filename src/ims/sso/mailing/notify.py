from datetime import datetime
from email.header import Header

import plone.api as api
from plone.base.interfaces.controlpanel import IMailSchema
from plone.base.utils import safe_text
from plone.registry.interfaces import IRegistry
from Products.Five import BrowserView
from zope.component import getMultiAdapter, getUtility

from ..interfaces import IMailTemplatesUtility, ISingleSignonUtility
from ..utility import registration_subject


class RegisteredNotify(BrowserView):
    def __call__(self, **kwargs):
        sso = getUtility(ISingleSignonUtility)
        portal_title = api.portal.get_registry_record("plone.site_title")
        mpt = getMultiAdapter((self.context, self.request), name="mail_relink_template")
        pw_reset = api.portal.get_tool("portal_password_reset")
        from_name = mpt.encoded_mail_sender()
        to_name = kwargs["member"].getProperty("email")
        subject = registration_subject(portal_title)

        registration_url = sso.get_url_registration()

        templater = getUtility(IMailTemplatesUtility)
        notify_form = templater.registered_notify()

        link_url = sso.get_url_linkaccount(
            link_key=kwargs["reset"]["randomstring"],
            userid=kwargs["member"].getId(),
        )
        timeout = pw_reset.getExpirationTimeout()
        timeout_d = kwargs["reset"]["expires"].strftime("%Y %b %d %I:%M %p")

        # do we need to do this or is it already done by RegistrationTool?
        reset = api.portal.get_tool("portal_password_reset")
        reset.requestReset(kwargs["member"].getId())

        params = {
            "from_name": from_name,
            "to_name": to_name,
            "subject": subject,
            "portal_title": portal_title,
            "registration_url": registration_url,
            "link_url": link_url,
            "userid": kwargs["member"].getId(),
            "timeout": timeout,
            "timeout_d": timeout_d,
            "curr_year": datetime.now().year,
        }
        return templater.mail_form(template=notify_form, params=params)


class MailRelink(RegisteredNotify):
    def encoded_mail_sender(self):
        """from Products.CMFPlone.browser.password_reset"""
        registry = getUtility(IRegistry)
        mail_settings = registry.forInterface(IMailSchema, prefix="plone")
        from_ = mail_settings.email_from_name
        mail = mail_settings.email_from_address
        return f'"{self.encode_mail_header(from_)}" <{mail}>'

    def encode_mail_header(self, text):
        """from Products.CMFPlone.browser.password_reset"""
        return Header(safe_text(text), "utf-8")

    def __call__(self, **kwargs):
        sso = getUtility(ISingleSignonUtility)
        portal_title = api.portal.get_registry_record("plone.site_title")
        pw_reset = api.portal.get_tool("portal_password_reset")
        from_name = self.encoded_mail_sender()
        to_name = kwargs["member"].getProperty("email")
        subject = f"Update Login service for {portal_title}"
        charset = kwargs["charset"]
        registration_url = sso.get_url_registration()

        templater = getUtility(IMailTemplatesUtility)
        password_form = templater.mail_relink()

        link_url = sso.get_url_linkaccount(
            link_key=kwargs["reset"]["randomstring"],
            userid=kwargs["member"].getId(),
        )
        timeout = pw_reset.getExpirationTimeout()
        timeout_d = kwargs["reset"]["expires"].strftime("%Y %b %d %I:%M %p")

        params = {
            "from_name": from_name,
            "to_name": to_name,
            "subject": subject,
            "charset": charset,
            "portal_title": portal_title,
            "registration_url": registration_url,
            "link_url": link_url,
            "timeout": timeout,
            "timeout_d": timeout_d,
            "curr_year": datetime.now().year,
        }
        return templater.mail_form(template=password_form, params=params)
