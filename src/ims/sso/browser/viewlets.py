from plone import api
from plone.app.layout.viewlets.common import ViewletBase
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile
from zope.annotation.interfaces import IAnnotations
from zope.component import getUtility

from ..configs import AUTHENTICATED_KEY
from ..controlpanels.sso import ISSOSettings
from ..interfaces import ISingleSignonUtility


class SsoWarningsViewlet(ViewletBase):
    """User is authenticated with SSO but has no active account here"""

    index = ViewPageTemplateFile("templates/warnings.pt")

    @property
    def sso(self):
        return getUtility(ISingleSignonUtility)

    def status(self):
        annotations = IAnnotations(self.request)
        if AUTHENTICATED_KEY in annotations:
            userid = annotations[AUTHENTICATED_KEY]
            user = api.user.get(userid)
            return user.getProperty("active")
        return "unknown"

    def site_admin(self):
        return api.portal.get_registry_record("ims.reply_to_address")

    def reactivation_url(self):
        return api.portal.get().absolute_url() + "/@@request_reactivation"

    def show_warning(self):
        """Show warning that the user is authenticated but unauthorized. Allows opt out by site"""
        try:
            registry_setting = api.portal.get_registry_record(interface=ISSOSettings, name="show_auth_unauth")
        except api.exc.InvalidParameterError:
            return True
        else:
            return bool(registry_setting)

    def is_inactive(self):
        """Option to reactivate own inactive account"""
        return self.status() == "inactive"

    def is_disabled(self):
        """Option to reactivate own inactive account"""
        return self.status() == "disabled"

    def show_alert(self):
        """General alert section for auth/unauth and/or reactivation"""
        # allow sites to opt out with registry setting
        if self.is_inactive() or self.show_warning():
            for _view in api.portal.get_registry_record(interface=ISSOSettings, name="unauth_ignored_views"):
                if _view in self.request["ACTUAL_URL"].split("/"):
                    return False
            if not str(self.request.response.status).startswith("2"):
                return False
            return self.sso.has_user_header(self.request) and api.user.is_anonymous() and not self.logingov()

    def logingov(self):
        # TODO - this needs to be moved to ims.users only
        #        override this as a browserlayer view there
        LOGIN_DOT_GOV_IDP_DOMAIN = "auth.ncats.nih.gov"
        LOGIN_DOT_GOV_DEV_IDP_DOMAIN = "a-ci.ncats.io"
        for _view in api.portal.get_registry_record(interface=ISSOSettings, name="unauth_ignored_views"):
            if _view in self.request["ACTUAL_URL"].split("/"):
                return False

        login_gov_domains = [LOGIN_DOT_GOV_DEV_IDP_DOMAIN, LOGIN_DOT_GOV_IDP_DOMAIN]
        sso = getUtility(ISingleSignonUtility)
        real_login_name = sso.get_login_from_request(self.request)
        if api.user.is_anonymous() and real_login_name:
            idp, _ = sso.extract_idp_login(real_login_name)
            if idp in login_gov_domains:
                shib_header_email = api.portal.get_registry_record(interface=ISSOSettings, name="shib_header_email")
                email = self.request.environ.get(shib_header_email)
                for usr in api.user.get_users():
                    # user is already converted but still anon - presumably because of status
                    is_login_gov = sso.extract_idp_login(usr.getUserName())[0] in login_gov_domains
                    if email == usr.getProperty("email", None) and not is_login_gov:
                        self.request.response.setHeader("Cache-Control", "no-cache")
                        self.request.response.setHeader("Pragma", "no-cache")
                        return True

    def login_info(self):
        sso = getUtility(ISingleSignonUtility)
        shib_header_email = api.portal.get_registry_record(interface=ISSOSettings, name="shib_header_email")
        real_login_name = sso.get_login_from_request(self.request)
        LOGIN_DOT_GOV_IDP_DOMAIN = "auth.ncats.nih.gov"
        LOGIN_DOT_GOV_DEV_IDP_DOMAIN = "a-ci.ncats.io"
        if real_login_name:
            idp, idp_login_name = sso.extract_idp_login(real_login_name)
            if idp in [LOGIN_DOT_GOV_DEV_IDP_DOMAIN, LOGIN_DOT_GOV_IDP_DOMAIN]:
                idp_login_name = self.request.environ.get(shib_header_email)
            idp = sso.get_idp_from_domain(idp)
            return f"{idp_login_name} via {idp}"
        else:
            return api.user.get_current().getId()
