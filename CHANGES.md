# ims.sso 1.1.6a9 (2026-11-23)

## Other tasks

- replace uv ([72033])

[72033]: https://squishlist.com/ims/plone/72033


# ims.sso 1.1.6a8 (2026-11-23)

## Other tasks

- replace uv ([72033])

[72033]: https://squishlist.com/ims/plone/72033


# ims.sso 1.1.6a7 (2026-11-23)

## Other tasks

- add text ([72033])

[72033]: https://squishlist.com/ims/plone/72033


# ims.sso 1.1.6a6 (2026-11-23)

## Other tasks

- [72033]

[72033]: https://squishlist.com/ims/plone/72033


# ims.sso 1.1.6a5 (2026-11-23)

## Other tasks

- [72033]

[72033]: https://squishlist.com/ims/plone/72033


# ims.sso 1.1.6a4 (2026-11-20)

## Other tasks

- [72033]

[72033]: https://squishlist.com/ims/plone/72033


# ims.sso 1.1.6a3 (2026-11-20)

No significant changes.


# ims.sso 1.1.6a2 (2026-11-18)

## Other tasks

- [72033]

[72033]: https://squishlist.com/ims/plone/72033


# ims.sso 1.1.6a1 (2026-11-18)

## Other tasks

- [72033]

[72033]: https://squishlist.com/ims/plone/72033


# ims.sso 1.1.5 (2026-11-10)

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
