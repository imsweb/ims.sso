import datetime

import plone.api
from Products.PluggableAuthService.events import PASEvent
from Products.PluggableAuthService.interfaces.events import IPASEvent
from zope.interface.declarations import implementer


class IUserRelinkedEvent(IPASEvent):
    """User relink initiated"""


@implementer(IUserRelinkedEvent)
class UserRelinkedEvent(PASEvent):
    """User relink intiated"""


def user_relinked(user):
    """user was relinked, reset the created_date. This resets the unlinked expiration mechanism"""
    user = plone.api.user.get(userid=user.principal["id"])
    today = datetime.date.today()
    user.setMemberProperties({"created_date": today})
