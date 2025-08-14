from . import controllers
from . import models

from odoo.addons.payment import setup_provider, reset_payment_provider

def post_init_hook(env):
    """
    This hook is called after the module installation.
    It setups the payment provider and configures the journal correctly.
    """
    setup_provider(env, 'tap')

    
def uninstall_hook(env):
    """Reset the acquirers of the module.
    This hook is called before the module uninstallation."""
    reset_payment_provider(env, 'tap')










