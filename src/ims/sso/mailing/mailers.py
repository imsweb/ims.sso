class BaseMailTemplates:
    title = "Base"

    def registered_notify(self):
        pass

    def mail_password(self):
        pass


class LoginDotGovMailTemplates(BaseMailTemplates):
    """Only the IMS service provider is available"""

    title = "Login.gov"

    def registered_notify(self):
        return """You ({to_name}) have been registered as a user on {portal_title}.

To log in to {portal_title}, you must use Login.gov.

Step 1: If you DON'T have a Login.gov account, please create one at https://login.gov/create-an-account/.
If you already have a Login.gov account, continue to Step 2.

Step 2: Link your Login.gov account with {portal_title} by following this link: {link_url}
"""

    def mail_password(self):
        return """Please update your login service for {portal_title} by linking a Login.gov account.

Step 1: If you DON'T have a Login.gov account, please create one at {logingov_registration_url}.
If you already have a Login.gov account, continue to Step 2.

Step 2: Link your Login.gov account with {portal_title} by following this link: {link_url}
"""


class NIHMailTemplates(BaseMailTemplates):
    """Only the NIH service provider is available"""

    title = "NIH"

    def registered_notify(self):
        return """You ({to_name}) have been registered as a user on {portal_title}.

This portal requires an NIH Network account.

Step 1: If you DON'T already have an NIH Network account, you will need to contact the NIH to create one.

Step 2: Link your NIH account with the portal using this link: {link_url}"""

    def mail_password(self):
        return """Please update your login service for {portal_title}.

This portal requires an NIH Network account.

Step 1: If you DON'T already have an NIH Network account, you will need to contact the NIH to create one.

Step 2: Link your NIH account with the portal using this link: {link_url}"""


class NIHLoginDotGovMailTemplates(BaseMailTemplates):
    """Both Login.gov and NIH service providers are available"""

    title = "Login.gov and NIH"

    def registered_notify(self):
        return """You ({to_name}) have been registered as a user on {portal_title}.

To log in to {portal_title}, you must use one of the following services:
- Login.gov
- NIH Network Login
- IMS Employee Login

Step 1: If you DON'T have an account with one of these services, please create a Login.gov account at
{logingov_registration_url}.
If you already have an account with one of the services above, continue to Step 2.

Step 2: Link your account with {portal_title} by following this link: {link_url}"""

    def mail_password(self):
        return """Please update your login service for {portal_title}.

To log in to {portal_title}, you must use one of the following services:
- Login.gov
- NIH Network Login
- IMS Employee Login

Step 1: If you DON'T have an account with one of these services, please create a Login.gov account at
{logingov_registration_url}.
If you already have an account with one of the services above, continue to Step 2.

Step 2: Link your account with {portal_title} by following this link: {link_url}"""


class CTEPMailTemplates(BaseMailTemplates):
    title = "CTEP"

    def registered_notify(self):
        return """You ({to_name}) have been registered as a user on {portal_title}.

This portal requires a CTEP-IAM account. If you do not have CTEP-IAM account please contact the site administrator
by replying to this message.

To link your CTEP-IAM account with the portal, use the following link:
{link_url}"""

    def mail_password(self):
        return """Please update your login service for {portal_title}.

This portal requires a CTEP-IAM account. If you do not have CTEP-IAM account please contact the site
administrator by replying to this message.

To link your CTEP-IAM account with the portal, use the following link:
{link_url}"""


class NoSSOMailTemplates(BaseMailTemplates):
    title = "No SSO"

    def registered_notify(self):
        return """You ({to_name}) have been registered as a user on {portal_title}.

Please activate your account by visiting {link_url}. Your user name is {userid}."""

    def mail_password(self):
        return """You are receiving this email because you or a site manager requested a password change on
{portal_title}.

Follow this link to reset your password: {link_url}"""


class ADFSMailTemplates(BaseMailTemplates):
    """Only the IMS Employee service provider is available"""

    title = "ADFS"

    def registered_notify(self):
        return """You ({to_name}) have been registered as a user on {portal_title}.

To activate your account, visit this link: {link_url}"""

    def mail_password(self):
        return """A request has been made to update your login service for {portal_title}.

Visit this link to update and reactive your account: {link_url}"""
