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
