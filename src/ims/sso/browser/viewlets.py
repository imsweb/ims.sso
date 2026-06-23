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
            return self.sso.has_user_header(self.request) and api.user.is_anonymous()

    def login_info(self):
        sso = getUtility(ISingleSignonUtility)
        real_login_name = sso.get_login_from_request(self.request)
        if real_login_name:
            idp, idp_login_name = sso.get_idp_domain_from_login(real_login_name)
            idp = sso.get_idp_from_domain(idp)
            return f"{idp_login_name} via {idp}"
        else:
            return api.user.get_current().getId()
