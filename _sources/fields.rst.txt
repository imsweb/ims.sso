User fields
===========

ims.sso creates the following fields

* ``first_name`` - updated from Shibboleth header
* ``last_name`` - updated from Shibboleth header. The user fullname will be created from these names
* ``created_date`` - this is used primarily for unlinked accounts. If the user never responds, the user account will be deleted after a period.
* ``active`` - the active status of the user, active, inactive, or disabled. This must be ``active`` to authenticate
* ``service`` - Service accounts are exempt from some maintenance tasks, like inactivity checks
* ``activation_date`` - the date the user last logged in, or was first activated. This is referenced for inactivity checks