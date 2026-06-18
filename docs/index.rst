===================================
ims.sso
===================================

Shibboleth and Plone integration

Goals:

* Plone user accounts must link to a single user from a single IdP
* Accounts have `status` which can be active, inactive, or disabled.
   * User accounts not actively being used are demoted in status based on days since last login (configurable) as a security measure
   * Inactive and Disabled accounts both fail authentication with Plone.
   * Inactive accounts can be auto-reactivated by verifying access to their email account. The default time to make inactive is 90 days.
   * Disabled accounts require Site Administrator action to be re-activated. The default time to make disabled is 2 years
   * Accounts can be manually disabled instead of deleting the user. This preserves various metadata.
   * Accounts marked as `service` are never demoted
* User's overview page is overhauled to support IdP identification and status


Contents:

.. toctree::
   :maxdepth: 2

   linking
   fields
   activation
   email
   browser

Test coverage:

   `<coverage>`_

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`