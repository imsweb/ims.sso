# ims.sso 1.2.0 (2026-11-24)

## Feature

- Use the full URL for IdP identification, not just domain ([72056])

[72056]: https://squishlist.com/ims/plone/72056


# ims.sso 1.1.6 (2026-11-24)

## Other tasks

- add towncrier to automatically update package version number ([72033])

[72033]: https://squishlist.com/ims/plone/72033


## Bug fix

- Add `_post_login` hook for REST API

# ims.sso 1.1.4 (2026-11-04)

## Bug fix

- run upgrade step to update `login` and `logout` in portal_actions

# ims.sso 1.1.1 (2026-11-04)

## Bug fix

- Fix redirect for single IdP to include a `target` parameter
- Fix portal_action `login` condition to check if already on the login page


# ims.sso 1.1.0 (2026-10-26)

## Breaking Change

- Change IdP registration from JSON to ZCML. This allows dynamic values and reduces the complexity of control panel settings.
- Fully embed login and logout logic in the @@login and @@logout views

## Bug fix
- Improve responsiveness for Users settings page

## Chore
- Add test to ensure service accounts can't be manually changed

# ims.sso 1.0.0 (2026-08-03)

- Initial release


# ims.sso 1.0.0a1 (2026-06-23)

## Feature

- Initial development
