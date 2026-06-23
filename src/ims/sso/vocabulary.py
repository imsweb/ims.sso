from zope.component import getUtilitiesFor
from zope.interface.declarations import provider
from zope.schema.interfaces import IVocabularyFactory
from zope.schema.vocabulary import SimpleTerm, SimpleVocabulary

from .configs import ACTIVE_STATUS, DISABLED_STATUS, INACTIVE_STATUS
from .interfaces import IMailTemplates


@provider(IVocabularyFactory)
def mail_idps(context):
    utilities = getUtilitiesFor(IMailTemplates)
    return SimpleVocabulary([SimpleTerm(value=util_id, title=util.title) for util_id, util in utilities])


@provider(IVocabularyFactory)
def active_status(context):
    return SimpleVocabulary([
        SimpleTerm(value=ACTIVE_STATUS, title="Active"),
        SimpleTerm(value=INACTIVE_STATUS, title="Inactive"),
        SimpleTerm(value=DISABLED_STATUS, title="Disabled"),
    ])
