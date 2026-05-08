from zope.i18nmessageid import MessageFactory

_ = MessageFactory("ims.sso")

APACHE_NULL = "(null)"


ACTIVE_STATUS = "active"
INACTIVE_STATUS = "inactive"
DISABLED_STATUS = "disabled"
REACTIVATE_VIEW_ID = "reactive_user"

# seconds between last update of login_time, so we don't update every request
# TODO - move this to a login session, so it's not needed?
LOGIN_UPDATE_THRESHOLD = 30 * 60

NOT_LINKED = "not.linked"

# recognized domains
ADFS_IDP_DOMAIN = "adfs.omni.imsweb.com"
NIH_IDP_DOMAIN = "auth.nih.gov"
NIH_DEV_IDP_DOMAIN = "authdev.nih.gov"
CTEP_IDP_DOMAIN = "iapps-ctep.nci.nih.gov"
LOGIN_DOT_GOV_IDP_DOMAIN = "auth.ncats.nih.gov"
LOGIN_DOT_GOV_DEV_IDP_DOMAIN = "a-ci.ncats.io"

IDP_FRIENDLY_NAMES = {
    NOT_LINKED: "Not Linked",
    ADFS_IDP_DOMAIN: "IMS Employee Login",
    NIH_IDP_DOMAIN: "NIH",
    NIH_DEV_IDP_DOMAIN: "NIH (dev)",
    CTEP_IDP_DOMAIN: "CTEP",
    LOGIN_DOT_GOV_DEV_IDP_DOMAIN: "Login.gov (dev)",
    LOGIN_DOT_GOV_IDP_DOMAIN: "Login.gov",
}

AUTHENTICATED_KEY = "ims.sso.login_annotation"

IMS_LOGIN_REGISTRATION_URL = "https://help.loginservice.imsweb.com/register?email={email}&fromURL={portal_url}"
LOGINGOV_REGISTRATION_URL = "https://login.gov/create-an-account/"

GENERIC_LOGOUT_URL = "https://help.loginservice.imsweb.com/logout"
ADFS_LOGOUT_URL = "https://adfs.omni.imsweb.com/adfs/ls/IdpInitiatedSignon.aspx"
NIH_LOGOUT_URL = "https://auth.nih.gov/advancedlogin/logout.asp"
NIH_DEV_LOGOUT_URL = "https://authdev.nih.gov/advancedlogin/logout.asp"
LOGIN_DOT_GOV_LOGOUT_URL = "https://secure.login.gov/api/saml/logout2024"
