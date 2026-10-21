===================================
ims.sso
===================================

Shibboleth and Plone integration

Goals:

* Plone user accounts must link to a single user from a single IdP
* Users must be explicitly authorized. Logging in with an IdP does not create a Plone account, you must be registered by an admin. Plone accounts are thus a subset of IdP accounts
* Accounts have **status** which aims to restrict access to accounts that may no longer need it.

   * User accounts must be ``active`` to pass authentication with Plone PAS (i.e. they can't login to Plone if not active)
   * User accounts not actively being used are demoted in status based on days since last login (configurable) as a security measure
   * Inactive accounts can be auto-reactivated by verifying access to their email account. The default time to make inactive is 90 days.
   * Disabled accounts require Site Administrator action to be re-activated. The default time to make disabled is 2 years
   * Accounts can be manually disabled instead of deleting the user. This preserves various metadata.
   * Accounts marked as ``service`` are never demoted

* User's overview page is overhauled to support active status searching and to display IdP information.


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