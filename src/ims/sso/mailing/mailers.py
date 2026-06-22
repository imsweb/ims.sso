class NoSSOMailTemplates:
    title = "No SSO"

    def registered_notify(self):
        return """You ({to_name}) have been registered as a user on {portal_title}.

Please activate your account by visiting {link_url}."""

    def mail_relink(self):
        return """You are receiving this email because you or a site manager requested a password change on
{portal_title}.

Follow this link to reset your password: {link_url}"""
