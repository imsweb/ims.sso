import datetime

import plone.api
from Products.PluggableAuthService.events import PASEvent
from Products.PluggableAuthService.interfaces.events import IPASEvent
from zope.interface.declarations import implementer


class IUserRelinkedEvent(IPASEvent):
    """An object has been downloaded"""


@implementer(IUserRelinkedEvent)
class UserRelinkedEvent(PASEvent):
    """An object has been downloaded"""


def user_relinked(user):
    """user was relinked, update created_date"""
    try:
        user = plone.api.user.get(userid=user.principal["id"])
    except plone.api.exc.CannotGetPortalError:
        return
    today = datetime.date.today()
    user.setMemberProperties({"created_date": today})
