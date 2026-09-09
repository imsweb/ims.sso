import logging

logger = logging.getLogger("ims.sso")


def login_actions(context):
    context.runImportStepFromProfile("ims.sso:default", "actions")
