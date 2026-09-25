from plone import api
from plone.protect import CheckAuthenticator, PostOnly
from plone.protect.interfaces import IDisableCSRFProtection
from Products.CMFPlone.PasswordResetTool import InvalidRequestError
from Products.Five import BrowserView
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile
from zope.annotation.interfaces import IAnnotations
from zope.component import getMultiAdapter, getUtility
from zope.event import notify
from zope.interface.declarations import alsoProvides, implementer
from zope.publisher.interfaces import IPublishTraverse

from ..configs import AUTHENTICATED_KEY, NOT_LINKED, _
from ..events import UserIdpUpdated
from ..interfaces import IReactivationUtility, ISingleSignonUtility


class Login(BrowserView):
    @property
    def sso(self):
        return getUtility(ISingleSignonUtility)

    def _get_idps(self, field, allow_redirect=False):
        _idps = [self.sso.idp_info[idp] for idp in field]
        if allow_redirect and len(_idps) == 1 and _idps[0].get("login"):
            self.request.response.redirect(_idps[0]["login"])
        return _idps

    def primary_idps(self):
        return self._get_idps(self.sso.get_setting("primary_idps") or [], not self.always_show)

    def secondary_idps(self):
        return self._get_idps(self.sso.get_setting("secondary_idps") or [])

    def all_idps(self):
        return (*self.primary_idps(), *self.secondary_idps())

    @property
    def always_show(self):
        return self.sso.get_setting("always_show_login")

    def from_address(self):
        return api.portal.get_registry_record(name="plone.email_from_address")

    def site_title(self):
        return api.portal.get_registry_record(name="plone.site_title")


class SsoLogout(BrowserView):
    @property
    def sso(self):
        return getUtility(ISingleSignonUtility)

    def __call__(self):
        self.context.restrictedTraverse("browser_id_manager").flushBrowserIdCookie()
        for cookie in self.request.cookies:
            self.request.response.setCookie(
                cookie,
                self.request.cookies[cookie],
                path="/",
                expires="Thu, 01 Jan 1970 00:00:00 GMT",
            )

        self.request.response.redirect(self.sso.get_url_logout(request=self.request))


@implementer(IPublishTraverse)
class SsoLinkaccount(BrowserView):
    def __init__(self, context, request):
        self.subpath = []
        super().__init__(context, request)

    def publishTraverse(self, request, name):
        self.subpath.append(name)
        return self

    def __call__(self):
        if not api.user.is_anonymous():
            # most likely a re-click or a tester
            return self.invalid_key()
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

        email = self.request.get(sso.get_setting("shib_header_email"))

        if login_name and email:
            pw_tool = api.portal.get_tool("portal_password_reset")
            try:
                pw_tool.verifyKey(key)
                password = sso.generate_password(user_id)  # random, unknown password
                pw_tool.resetPassword(user_id, key, password)
            except InvalidRequestError:
                return self.invalid_key()

            try:
                sso.set_login_name(user_id, login_name)
            except ValueError:  # likely duplicate
                return self.disallowed()
            else:
                sso.send_portal_link(email)
                usr = api.user.get(userid=user_id)  # we must reinstantiate after change
                if is_relink:
                    plone_view = getMultiAdapter((self.context, self.request), name="plone")
                    sso.notify_relinked(usr, email, plone_view)
                    notify(UserIdpUpdated(usr))
            return self.success()
        else:
            return self.request.response.redirect(
                f"{api.portal.get().absolute_url()}/login?came_from={self.request.URL}"
            )

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
            return api.portal.get().absolute_url()
        login_url = acl.ims_sso_plugin.login_url(api.portal.get().absolute_url())
        return login_url


class LoginCondition(BrowserView):
    def __call__(self):
        if not api.user.is_anonymous():  # sanity fallback
            return False
        sso = getUtility(ISingleSignonUtility)
        return not sso.is_shibboleth_authenticated(self.request)


class Logout(BrowserView):
    @property
    def sso(self):
        return getUtility(ISingleSignonUtility)

    def __call__(self, *args, **kwargs):
        self.request.response.redirect(self.sso.get_url_logout(self.request))


class RequireLoginView(BrowserView):
    def __call__(self, *args, **kw):

        utility = getUtility(ISingleSignonUtility)

        if utility.is_plone_authenticated():
            return api.content.get_view(
                context=api.portal.get(),
                request=self.request,
                name="insufficient-privileges",
            )()
        else:
            if utility.is_shibboleth_authenticated(self.request):
                return api.content.get_view(
                    context=self.context,
                    request=self.request,
                    name="unauthorized_shib_authenticated",
                )()
            else:
                return api.content.get_view(
                    context=self.context,
                    request=self.request,
                    name="unauthorized_shib_unauthenticated",
                )()


class RequestReactivation(BrowserView):
    def render(self):
        PostOnly(self.request)
        CheckAuthenticator(self.request)

        util = getUtility(IReactivationUtility)
        portal = api.portal.get()
        portal_url = portal.absolute_url()

        _key = util.request_reactivation()
        if not _key:
            api.portal.show_message(
                message="An activation key could not be obtained, contact the site administrator",
                type="error",
            )
            self.request.response.redirect(portal_url)
            return
        _key, expiry = _key
        expiry = api.portal.get_tool("translation_service").ulocalized_time(expiry, long_format=1)

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
