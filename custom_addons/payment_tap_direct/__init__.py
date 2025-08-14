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











# # Configure the journal to prevent the ValidationError
    # tap_provider = env.ref('payment_tap.payment_provider_tap', raise_if_not_found=False)
    # if tap_provider:
    #     # Find the journal associated with the provider
    #     journal = env['account.journal'].search([
    #         ('company_id', '=', tap_provider.company_id.id),
    #         ('code', '=', 'tap') # Default code given by setup_provider
    #     ], limit=1)
        
    #     # Find the tap payment method
    #     payment_method = env.ref('payment_tap.payment_method_tap', raise_if_not_found=False)
        
    #     if journal and payment_method:
    #         # Check if the payment method line already exists
    #         existing_line = env['account.payment.method.line'].search([
    #             ('journal_id', '=', journal.id),
    #             ('payment_method_id', '=', payment_method.id),
    #         ])
    #         if not existing_line:
    #             # Create the payment method line for inbound payments
    #             env['account.payment.method.line'].create({
    #                 'journal_id': journal.id,
    #                 'payment_method_id': payment_method.id,
    #             })
