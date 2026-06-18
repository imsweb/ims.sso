from zope.i18nmessageid import MessageFactory

_ = MessageFactory("ims.sso")

APACHE_NULL = "(null)"


ACTIVE_STATUS = "active"
INACTIVE_STATUS = "inactive"
DISABLED_STATUS = "disabled"
REACTIVATE_VIEW_ID = "reactive_user"

# seconds between last update of login_time, so we don't update every request
LOGIN_UPDATE_THRESHOLD = 30 * 60

NOT_LINKED = "not.linked"

AUTHENTICATED_KEY = "ims.sso.login_annotation"
