import plone.api
from Products.Five import BrowserView
from zope.component import getUtility

from ..interfaces import ISingleSignonUtility


class Unauthorized(BrowserView):
    def email_from_address(self):
        return plone.api.portal.get_registry_record("plone.email_from_address")

    def login_info(self):
        sso = getUtility(ISingleSignonUtility)
        real_login_name = sso.get_login_from_request(self.request)
        if real_login_name:
            idp, idp_login_name = sso.extract_idp_login(real_login_name)
            idp = sso.get_idp_from_domain(idp)
            return f"{idp_login_name} via {idp}"
        else:
            return plone.api.user.get_current().getId()
