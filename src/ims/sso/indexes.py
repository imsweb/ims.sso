from plone.indexer import indexer
from zope.interface import Interface


@indexer(Interface)
def owner_indexer(obj):
    for userid, roles in list(obj.__ac_local_roles__.items()):
        if "Owner" in roles:
            return userid
