import logging

logger = logging.getLogger("ims.sso")


def to_2(context):
    context.runImportStepFromProfile("ims.sso:default", "actions")
    context.runImportStepFromProfile("ims.sso:default", "plone.app.registry")
