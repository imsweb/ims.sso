import logging

from ims.graylog.subscribers import get_logger
from plone import api
from plone.protect import CheckAuthenticator, PostOnly
from plone.protect.interfaces import IDisableCSRFProtection
from Products.CMFPlone.browser.login.login import LoginForm
from Products.CMFPlone.PasswordResetTool import InvalidRequestError
from Products.Five import BrowserView
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile
from zope.annotation.interfaces import IAnnotations
from zope.component import getMultiAdapter, getUtility
from zope.interface.declarations import alsoProvides, implementer
from zope.publisher.interfaces import IPublishTraverse

from ..configs import AUTHENTICATED_KEY, NOT_LINKED, _
from ..interfaces import IReactivationUtility, ISingleSignonUtility


class LoginFilter(logging.Filter):
    def filter(self, record):
        record.application = "Plone"

        record.subproject = "bad_login"
        record.portal = api.portal.get().getId()
        return True


class RedirectLogin(LoginForm):
    """This is the Plone default login page. SSO sites do not use it."""

    def __call__(self):
        self.request.response.redirect(api.portal.get().absolute_url())
        return

        # TODO - alternatively this could create a session
        # we would need to update the auth/unauth check


class SsoLogout(BrowserView):
    def sso(self):
        return getUtility(ISingleSignonUtility)

    def __call__(self):
        return
        # TODO - do not use for no-session. For session, delete cookie
        # self.context.restrictedTraverse("browser_id_manager").flushBrowserIdCookie()
        # for cookie in self.request.cookies:
        #     self.request.response.setCookie(
        #         cookie,
        #         self.request.cookies[cookie],
        #         path="/",
        #         expires="Thu, 01 Jan 1970 00:00:00 GMT",
        #     )

        # self.request.response.redirect(self.sso().get_url_logout(request=self.request))


@implementer(IPublishTraverse)
class SsoLinkaccount(BrowserView):
    def __init__(self, context, request):
        self.subpath = []
        super().__init__(context, request)

    def publishTraverse(self, request, name):
        self.subpath.append(name)
        return self

    def __call__(self):
        alsoProvides(self.request, IDisableCSRFProtection)
        sso = getUtility(ISingleSignonUtility)
        try:
            key = self.subpath[0]
            user_id = self.subpath[1]
        except IndexError:
            return self.invalid_key()

        usr = api.user.get(userid=user_id)
        is_relink = usr and NOT_LINKED not in usr.getUserName()
        login_name = sso.get_login_from_request(self.request)
        email = self.request.get("HTTP_SHIBEMAIL")

        if login_name and email:
            pw_tool = api.portal.get_tool("portal_password_reset")
            try:
                pw_tool.verifyKey(key)
                link_key = sso.generate_key(user_id)
                pw_tool.resetPassword(user_id, key, link_key)
            except InvalidRequestError:
                return self.invalid_key()

            try:
                sso.set_login_name(user_id, login_name)
                sso.send_portal_link(email)
                usr = api.user.get(userid=user_id)  # we must reinstatiate after change
                if is_relink:
                    plone_view = getMultiAdapter((self.context, self.request), name="plone")
                    sso.notify_relinked(usr, email, plone_view)
                    logger = get_logger()
                    logger.info(
                        "User account IdP updated",
                        extra={"actor": usr.getId(), "principal": usr.getId()},
                    )
                # member = api.user.get(userid=user_id)
                # do we need to do this here, or will login get it?
                # sso.update_member_from_request(self.request, member)
            except ValueError:  # likely duplicate
                # I don't know why we need this but https://www.squishlist.com/ims/plone/67528/#comment-945834
                return self.disallowed()
            return self.success()
        else:
            return ViewPageTemplateFile("templates/linkaccount_anonymous.pt")(self)

    def disallowed(self):
        return ViewPageTemplateFile("templates/linkaccount_disallowed.pt")(self)

    def success(self):
        return ViewPageTemplateFile("templates/linkaccount_finish.pt")(self)

    def invalid_key(self):
        username = api.user.get_current().getUserName()
        if username != "Anonymous User":
            api.portal.show_message(
                _(
                    "Invalid or expired key. No accounts were linked, but you are already logged in. Please update "
                    "your bookmark to this page."
                ),
                self.request,
                type="warning",
            )
            return self.request.response.redirect(api.portal.get().absolute_url())
        else:
            return ViewPageTemplateFile("templates/linkaccount_invalid.pt")(self)


class LoginUrl(BrowserView):
    def __call__(self):
        acl = api.portal.get_tool("acl_users")
        if "ims_sso_plugin" not in acl.objectIds():
            return self.portal_url
        login_url = acl.ims_sso_plugin.login_url(self.request.ACTUAL_URL)
        # this is ugly and probably should be handled by the challenge plugin instead
        # trying to make it not redirect to an unauthorized page after they log in
        if "target=" in login_url and self.request.get("came_from"):
            return login_url.split("target=")[0] + "target=" + self.request["came_from"]
        else:
            return login_url


class LoginCondition(BrowserView):
    def __call__(self):
        if not api.user.is_anonymous():  # sanity fallback
            return False
        return not [c for c in list(self.request.cookies.keys()) if "shibsession" in c]


class LogoutUrl(BrowserView):
    def __call__(self):
        return f"{api.portal.get().absolute_url()}/sso-logout"


class RequireLoginView(BrowserView):
    def __call__(self, *args, **kw):

        portal_state = getMultiAdapter(
            (self.context, self.request),
            name="plone_portal_state",
        )
        portal = portal_state.portal()

        utility = getUtility(ISingleSignonUtility)

        if portal_state.anonymous():
            # logged in through SSO, but anonymous to this site
            if utility.no_challenge_header(self.request):
                return getMultiAdapter((self.context, self.request), name="unauthorized")()
            else:
                return getMultiAdapter((self.context, self.request), name="unauthorized_anonymous")()
        else:
            return getMultiAdapter((portal, self.request), name="insufficient-privileges")()


class RequestReactivation(BrowserView):
    def render(self):
        PostOnly(self.request)
        CheckAuthenticator(self.request)

        util = getUtility(IReactivationUtility)
        _key, expiry = util.request_reactivation()
        expiry = api.portal.get_tool("translation_service").ulocalized_time(expiry, long_format=1)

        portal = api.portal.get()
        portal_url = portal.absolute_url()
        if not _key:
            api.portal.show_message(
                message="An activation key could not be obtained, contact the site administrator",
                type="error",
            )
            self.request.response.redirect(portal_url)
            return
        reg_link = f"{portal_url}/reactivate_user/{_key}"
        portal_title = api.portal.get_registry_record("plone.site_title")
        msg = (
            f"You are receiving this because you requested to have your account on {portal_title} \
reactivated. To reactivate your account, visit {reg_link}.\n\n"
            f"This link will expire in 1 day (by {expiry}). If the link expires, log into {portal_url} and "
            f"reactivate your account again.\n\n"
            f"If you did not initiate this action, you may ignore this message."
        )
        user_id = IAnnotations(self.request)[AUTHENTICATED_KEY]
        api.portal.send_email(
            recipient=api.user.get(user_id).getProperty("email"),
            subject=f"Reactivate your account for {portal_title}",
            body=msg,
            immediate=False,
        )
        api.portal.show_message(
            "An email with a link to reactivate your account has been sent to the address "
            "associated with your account. If you do not receive the email, contact the "
            f"<a href='{api.portal.get().absolute_url()}/contact-info'>site "
            "administrator</a>."
        )
        self.request.response.redirect(portal_url + "/reactivation")
        return


class ReactivateUserAccount(BrowserView):
    def __init__(self, context, request):
        self.subpath = []
        super().__init__(context, request)

    def publishTraverse(self, request, name):
        self.subpath.append(name)
        return self

    def __call__(self):
        util = getUtility(IReactivationUtility)
        try:
            key = self.subpath[0]
        except IndexError:
            api.portal.show_message(
                "Sorry, this appears to be an invalid request. Please make sure you copied "
                "the URL exactly as it appears in your email.",
                type="warning",
            )
            self.request.response.redirect(api.portal.get().absolute_url() + "/reactivation")
            return
        status = util.reactivate_user(key)
        if status:
            api.portal.show_message("Your account has been successfully reactivated.")
            self.request.response.redirect(api.portal.get().absolute_url())
        else:
            if not api.user.is_anonymous():
                # the activation key is invalid but the user is authenticated. They are probably visiting using
                # the reactivation email link, after already doing that step.
                self.request.response.redirect(api.portal.get().absolute_url())
                return

            api.portal.show_message(
                "Your account could not be activated. This may "
                "be due to an invalid or expired reactivation link, or "
                "your account may have been disabled after the reactivation link was sent. "
                f'Contact the <a href="{api.portal.get().absolute_url()}/contact-info">'
                "site administrator</a> for help with accessing the site.",
                type="error",
            )
            self.request.response.redirect(api.portal.get().absolute_url() + "/reactivation")
