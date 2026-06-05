import plone.api
from DateTime import DateTime
from plone.api.portal import send_email
from plone.autoform.form import AutoExtensibleForm
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile
from z3c.form import button, form
from zope.component import getUtility
from zope.event import notify

from ..configs import NOT_LINKED, _
from ..events import UserRelinkedEvent
from ..interfaces import IMailTemplatesUtility, IMassRelink, ISingleSignonUtility
from ..utility import registration_subject


class MassRelink(AutoExtensibleForm, form.Form):
    """Sends out a reminder email to all unlinked users. Typical usage would be after mass registration on a new site."""

    ignoreContext = True
    schema = IMassRelink
    template = ViewPageTemplateFile("mass_relink.pt")

    @button.buttonAndHandler(_("Send It"), name="send")
    def email_unlinked(self, action) -> None:
        portal = plone.api.portal.get()
        portal_title = plone.api.portal.get_registry_record("plone.site_title")
        reset = plone.api.portal.get_tool("portal_password_reset")

        from_name = plone.api.portal.get_registry_record("plone.email_from_address")
        subject = registration_subject(portal_title)

        sso = getUtility(ISingleSignonUtility)

        for user_id in self.unlinked_users():
            member = plone.api.user.get(user_id)
            to_name = member.getProperty("email")

            retval = reset.requestReset(user_id)
            registration_email = sso.get_url_registration()
            randomstring = retval["randomstring"]
            link_url = sso.get_url_linkaccount(link_key=randomstring, userid=user_id)

            timeout = reset.getExpirationTimeout()
            timeout_d = (DateTime() + timeout).aCommonZ()

            templater = getUtility(IMailTemplatesUtility)
            notify_form = templater.registered_notify()

            params = {
                "from_name": from_name,
                "to_name": to_name,
                "subject": subject,
                "portal_title": portal_title,
                "registration_email": registration_email,
                "userid": user_id,
                "link_url": link_url,
                "timeout": timeout,
                "timeout_d": timeout_d,
            }

            notify(UserRelinkedEvent({"id": user_id}))

            message = templater.mail_form(template=notify_form, params=params)
            send_email(
                sender=from_name,
                recipient=to_name,
                subject=subject,
                body=message,
                immediate=False,
            )

        plone.api.portal.show_message(message=_("msg_email", default="Emails sent"), request=self.request, type="info")
        self.request.response.redirect(portal.absolute_url())

    def duplicates(self) -> list[str]:
        """Warn about multiple users with the same email address"""
        emails = []
        dups = []
        for user in self.unlinked_user_data():
            if user["email"] in emails and user["email"] not in dups:
                dups.append(user["email"])
            emails.append(user["email"])
        return dups

    def unlinked_user_data(self) -> list[dict]:
        """Get name and email for all unlinked users"""
        data = []
        for user in plone.api.user.get_users():
            if NOT_LINKED in user.getUserName():
                email = user.getProperty("email")
                title = user.getProperty("fullname")
                data.append({"title_or_id": title or user.getId(), "email": email})
        return data

    def unlinked_users(self) -> list[str]:
        """Get unlinked users"""
        return [user.getId() for user in plone.api.user.get_users() if NOT_LINKED in user.getUserName()]
