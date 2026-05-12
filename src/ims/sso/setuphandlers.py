from plone import api
from plone.schemaeditor import interfaces
from plone.schemaeditor.fields import FieldFactory
from plone.schemaeditor.utils import FieldAddedEvent, IEditableSchema
from Products.PluggableAuthService.interfaces.plugins import (
    IAuthenticationPlugin,
    IChallengePlugin,
    IExtractionPlugin,
)
from zope.component import getAdapters
from zope.event import notify
from zope.lifecycleevent import ObjectAddedEvent
from zope.schema import Bool, Choice, Date, TextLine

from .configs import _


def configure_plugin():
    acl = api.portal.get_tool("acl_users")
    plugins = acl["plugins"]
    plugin_id = "ims_sso_plugin"

    if plugin_id not in acl.objectIds():
        # add
        constructors = acl.manage_addProduct["ims.sso"]
        constructors.manage_addImsSso(plugin_id, title="IMS SSO Plugin")

        # activate
    if plugin_id not in plugins.listPluginIds(IExtractionPlugin):
        plugins.activatePlugin(IExtractionPlugin, plugin_id)
    if plugin_id not in plugins.listPluginIds(IChallengePlugin):
        plugins.activatePlugin(IChallengePlugin, plugin_id)
    if plugin_id not in plugins.listPluginIds(IAuthenticationPlugin):
        plugins.activatePlugin(IAuthenticationPlugin, plugin_id)
    # if plugin_id not in plugins.listPluginIds(IUserEnumerationPlugin):
    #     plugins.activatePlugin(IUserEnumerationPlugin, plugin_id)

    # Make the Challenge plugin the first in the list:
    for _i in range(list(plugins.listPluginIds(IChallengePlugin)).index(plugin_id)):
        plugins.movePluginsUp(IChallengePlugin, [plugin_id])


def setup_various(context):
    """Miscellaneous steps import handle"""
    configure_plugin()
    setup_user_schema()


def add_user_field(field: dict):
    """adds user field to TTW schema"""
    context = api.portal.get().restrictedTraverse("member-fields")
    for schemata in [v for k, v in getAdapters((context,), interfaces.IFieldEditorExtender)]:
        factory = field["factory"]
        field_obj = factory(**field["data"])
        schemata(field_obj).forms = field["forms"]

        schema = IEditableSchema(context.schema)
        try:
            schema.addField(field_obj)
        except ValueError:
            schema.removeField(field["data"]["__name__"])
            schema.addField(field_obj)
        notify(ObjectAddedEvent(field_obj, context.schema))
        notify(FieldAddedEvent(context, field_obj))


def setup_user_schema():
    fields = [
        {
            "data": {
                "description": "The first name of the user",
                "title": "First Name",
                "required": False,
                "__name__": "first_name",
            },
            "factory": FieldFactory(TextLine, _("label_textline_field", default="Text line (String)")),
            "forms": ["On Registration", "In User Profile"],
        },
        {
            "data": {
                "description": "The last name of the user",
                "title": "Last Name",
                "required": True,
                "__name__": "last_name",
            },
            "factory": FieldFactory(TextLine, _("label_textline_field", default="Text line (String)")),
            "forms": ["On Registration", "In User Profile"],
        },
        {
            "data": {
                "description": "The day the user was registered",
                "title": "Created Date",
                "required": False,
                "__name__": "created_date",
            },
            "factory": FieldFactory(Date, _("label_date_field", default="Date")),
            "forms": [],
        },
        {
            "data": {
                "description": "activated/deactivated",
                "title": "Active status",
                "required": True,
                "__name__": "active",
            },
            "factory": FieldFactory(Choice, title="Active Status", vocabulary="ims.sso.active_status"),
            "forms": ["On Registration"],
        },
        {
            "data": {
                "description": "Service accounts have different security settings.",
                "title": "Service Account",
                "required": False,
                "__name__": "service",
            },
            "factory": FieldFactory(Bool, title="Service Account"),
            "forms": [],
        },
        {
            "data": {
                "description": "This date is used to determine when an account should be deactivated or disabled.",
                "title": "Activation Date",
                "required": False,
                "__name__": "activation_date",
            },
            "factory": FieldFactory(Date, title="Service Account"),
            "forms": [],
        },
    ]
    for field in fields:
        add_user_field(field)
