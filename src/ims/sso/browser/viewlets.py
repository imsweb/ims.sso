from plone import api
from plone.app.layout.viewlets.common import ViewletBase
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile
from zope.component import getUtility

from ..interfaces import IReactivationUtility, ISingleSignonUtility


class SsoWarningsViewlet(ViewletBase):
    """User is authenticated with SSO but has no active account here"""

    index = ViewPageTemplateFile("templates/warnings.pt")

    @property
    def sso(self):
        return getUtility(ISingleSignonUtility)

    def status(self):
        return getUtility(IReactivationUtility).current_user_status()

    def reactivation_url(self):
        return api.portal.get().absolute_url() + "/@@request_reactivation"

    def show_warning(self):
        """Show warning that the user is authenticated but unauthorized. Allows opt out by site"""
        return self.sso.get_setting("show_auth_unauth")

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
            for _view in self.sso.get_setting("unauth_ignored_views"):
                if _view == self.view.__name__:
                    return False
            if not str(self.request.response.status).startswith("2"):
                return False
            return self.sso.has_user_header(self.request) and api.user.is_anonymous() and not self.logingov()

    def logingov(self):
        # TODO - this needs to be moved to ims.users only
        #        override this as a browserlayer view there
        LOGIN_DOT_GOV_IDP_DOMAIN = "auth.ncats.nih.gov"
        LOGIN_DOT_GOV_DEV_IDP_DOMAIN = "a-ci.ncats.io"
        for _view in self.sso.get_setting("unauth_ignored_views"):
            if _view in self.request["ACTUAL_URL"].split("/"):
                return False

        login_gov_domains = [LOGIN_DOT_GOV_DEV_IDP_DOMAIN, LOGIN_DOT_GOV_IDP_DOMAIN]
        sso = getUtility(ISingleSignonUtility)
        real_login_name = sso.get_login_from_request(self.request)
        if api.user.is_anonymous() and real_login_name:
            idp, _ = sso.get_idp_domain_from_login(real_login_name)
            if idp in login_gov_domains:
                shib_header_email = self.sso.get_setting("shib_header_email")
                email = self.request.environ.get(shib_header_email)
                for usr in api.user.get_users():
                    # user is already converted but still anon - presumably because of status
                    is_login_gov = sso.get_idp_domain_from_login(usr.getUserName())[0] in login_gov_domains
                    if email == usr.getProperty("email", None) and not is_login_gov:
                        self.request.response.setHeader("Cache-Control", "no-cache")
                        self.request.response.setHeader("Pragma", "no-cache")
                        return True

    def login_info(self):
        # TODO - also override this in ims.users to display email address instead of user id
        sso = getUtility(ISingleSignonUtility)
        # shib_header_email = sso.get_setting("shib_header_email")
        real_login_name = sso.get_login_from_request(self.request)
        # LOGIN_DOT_GOV_IDP_DOMAIN = "auth.ncats.nih.gov"
        # LOGIN_DOT_GOV_DEV_IDP_DOMAIN = "a-ci.ncats.io"
        if real_login_name:
            idp, idp_login_name = sso.get_idp_domain_from_login(real_login_name)
            # if idp in [LOGIN_DOT_GOV_DEV_IDP_DOMAIN, LOGIN_DOT_GOV_IDP_DOMAIN]:
            #     idp_login_name = self.request.environ.get(shib_header_email)
            idp = sso.get_idp_from_domain(idp)
            return f"{idp_login_name} via {idp}"
        else:
            return api.user.get_current().getId()
