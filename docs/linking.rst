Linking accounts
=====================

The major underlying philosophy of this addon is Plone user accounts must be linked to a single Identity Provider (IdP) account via
Shibboleth headers.

PluggableAuthService has a distinction between login name and user id. It should be noted that Plone generally treats
these as identical. It is still possible to use login names in Plone, but some interface changees may be preferred for UX.

To ensure login names are unique, the IdP domain is used as a namespace. For example, a user
with user id `user1` logs in with a service that sends the Shibboleth IdP header as `myidp.foobar.com` and Shibboleth user header
as `myuser`. The Plone user id remains `user1` while the login name is `myuser@myidp.foobar.com`. Consider 
another site user logging in with a different service that also returns the user header as `myuser`. Without the IdP
namespace they would have been able to access the first user's account.

Registration
------------

A site admin that adds a user probably does not know the details of that user's IdP account, or maybe even what IdP
that user will use. Thus, we need a process to link a Plone account to an IdP account. On user registration,
the user is sent an email (see `Email Messages <email.html>`_) with a URL to link their account. This process is
similar to the reset password feature, and in fact uses the PasswordResetTool to generate a unique key for that user.
When visiting the site from that URL they will first be directed through Shibboleth, either by the challenge plugin
or by virtue of Apache/Nginx settings. The `@@linkaccount` consumes and invalidates the key and updates the user's login
name with data from the Shibb headers.

Before registration is complete, users will be given a unique, unsable login name. The domain is always @not.linked to allow
unlinked users to be easily identified.

Re-linking accounts
-------------------

Re-linking uses the same process as registration, except that the email instructions may be different. Login names
are NOT changed until the relink unique key is consumed.