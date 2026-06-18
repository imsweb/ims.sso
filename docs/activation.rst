Auto Re-Activation
=====================

Users with the `inactive` status are allowed to auto reactivate. To do so they effectively have to re-verify
they have access to the associated email address.

User Workflow
-------------

From the user's perspective the process is fairly low impact.
1. User is Anonymous to Plone
2. User is shown a warning that they are inactive, with a link to reactivate
3. User receives email and clicks the link in the email
4. User is now active, and authenticated/authorized

Backend
-------

Under the hood, things are more complicated. 
1. Authenticate Credentials plugin fails. But it stores the Shibb headers in the request annotations for convenience
2. Challenge plugin detects that the user is Shibboleth authenticated, so it does not redirect
3. Warning viewlets detect:
  1. User is Shibb authenticated but anonymous to Plone
  2. User account is inactive.