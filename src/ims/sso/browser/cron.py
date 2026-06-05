from plone.protect.interfaces import IDisableCSRFProtection
from Products.Five import BrowserView
from zope.component import getUtility
from zope.interface.declarations import alsoProvides

from ..interfaces import IReactivationUtility, ISingleSignonUtility


class PeriodicTasks(BrowserView):
    """This should be called by a cron job. It does three things
    1. Users that have not been linked since X days will be deleted
    2. Users who have not logged in in Y days will have their accounts disabled
    3. Remove expired annotations
    """

    def __call__(self, *args, **kwargs):
        alsoProvides(self.request, IDisableCSRFProtection)
        sso = getUtility(ISingleSignonUtility)
        react = getUtility(IReactivationUtility)
        sso.purge_unlinked()
        sso.disable_user_accounts()
        react.purge_activation_keys()
        return "User accounts updated."
