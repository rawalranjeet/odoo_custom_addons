/** @odoo-module **/

import { _t } from '@web/core/l10n/translation';
import { loadJS } from '@web/core/assets';
import paymentForm from '@payment/js/payment_form';
import { rpc } from "@web/core/network/rpc";

paymentForm.include({

    // #=== DOM MANIPULATION ===#

    /**
     * Prepare the inline form for Tap by creating the card element.
     */
    async _prepareInlineForm(providerId, providerCode, paymentOptionId, paymentMethodCode, flow) {
        if (providerCode !== 'tap') {
            await this._super(...arguments);
            return;
        }

        await this._super(...arguments);
        this._setPaymentFlow('direct');

        if (typeof goSell === 'undefined') {
            const radio = document.querySelector(`input[name="o_payment_radio"][data-provider-id="${providerId}"]`);
            const inlineForm = this._getInlineForm(radio);
            const tapContainer = inlineForm.querySelector('[name="o_tap_element_container"]');
            const tapInlineFormValues = JSON.parse(tapContainer.dataset.tapInlineFormValues);
            
            const tap_publishable_key = tapInlineFormValues.publishable_key;
            if (!tap_publishable_key) {
                this._displayErrorDialog(_t("Configuration Error"), _t("The publishable key for Tap is not configured."));
                return;
            }
            await loadJS("https://goSellJSLib.b-cdn.net/v2.0.0/js/gosell.js");
            this._initTapForm(tap_publishable_key);
        }
    },

    /**
     * Initialize the Tap goSellElements form.
     */
    _initTapForm(publishableKey) {
        goSell.goSellElements({
            containerID: 'element-container',
            gateway: {
                publicKey: publishableKey,
                language: "en",
                supportedPaymentMethods: "all",
                notifications: 'standard',
                labels: {
                    cardNumber: "Card Number",
                    expirationDate: "MM/YY",
                    cvv: "CVV",
                    cardHolder: "Name on Card",
                },
                style: {
                    base: {
                        color: '#535353', lineHeight: '18px', fontFamily: 'sans-serif',
                        fontSmoothing: 'antialiased', fontSize: '16px',
                        '::placeholder': { color: 'rgba(0, 0, 0, 0.26)', fontSize:'15px' }
                    },
                    invalid: { color: 'red' }
                },
                callback: (response) => {
                    if (response.error) {
                        this._displayErrorDialog(_t("Payment Error"), response.error.message);
                        this._enableButton(true);
                    } else {
                        this._createCharge(response.id);
                    }
                }
            }
        });
    },

    // #=== PAYMENT FLOW ===#

    /**
     * Process the direct payment flow for Tap by submitting the form.
     */
    async _processDirectFlow(providerCode, paymentOptionId, paymentMethodCode, processingValues) {
        if (providerCode !== 'tap') {
            this._super(...arguments);
            return;
        }

        this._disableButton(true);
        this.paymentContext.reference = processingValues.reference;
        goSell.submit();
    },

    /**
     * Create the charge on the backend using the token.
     */
    async _createCharge(tokenId) {
        try {
            const response = await rpc(
                '/payment/tap/create_charge',
                {
                    "reference": this.paymentContext.reference,
                    "token_id": tokenId
                },
            );

            if (response.success === true) {
                if (response.three_ds_redirect_url) {
                    window.location = response.three_ds_redirect_url;
                } else {
                    window.location = '/payment/status';
                }
            } else {
                this._displayErrorDialog(_t("Server Error"), response.error || _t("An unknown error occurred."));
                this._enableButton(true);
            }
        } catch (error) {
            this._displayErrorDialog(_t("Technical Error"), _t("An error occurred while creating the charge."));
            this._enableButton(true);
        }
    }
});