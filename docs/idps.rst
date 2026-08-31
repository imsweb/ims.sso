Register IdPs with ZCML
=======================

IdPs can be registered to provide information and instructions to specific users. Register with ZCML:

.. code-block:: xml

    <utility
        factory=".idps.Nih"
        provides="ims.sso.interfaces.ISsoIdp"
        name="auth.nih.gov"
        />


The utility name should be the domain given by the Shibboleth header e.g. HTTP_SHIBIDP