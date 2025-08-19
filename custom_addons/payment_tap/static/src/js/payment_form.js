/** @odoo-module **/

import { _t } from '@web/core/l10n/translation';
import { loadJS, loadCSS } from '@web/core/assets';
import paymentForm from '@payment/js/payment_form';
import { rpc } from "@web/core/network/rpc";


paymentForm.include({
    tapEventListenerAdded: false,
    
    // #=== DOM MANIPULATION ===#

    /**
     * Prepare the inline form for Tap by creating the card element.
     */
    async _prepareInlineForm(providerId, providerCode, paymentOptionId, paymentMethodCode, flow) {

        await this._super(...arguments);

        if (providerCode !== 'tap') {
            return;
        }

       

        const radio = document.querySelector('input[name="o_payment_radio"]:checked');
        const inlineForm = this._getInlineForm(radio);
        const tapContainer = inlineForm.querySelector('[name="o_tap_element_container"]');
        const tapInlineFormValues = JSON.parse(tapContainer.dataset.tapInlineFormValues);
        
        const tap_publishable_key = tapInlineFormValues.publishable_key;
        const tap_payment_flow_type = tapInlineFormValues.tap_payment_flow_type

        if (tap_payment_flow_type === 'redirect'){
            return;
        }
        
        this._setPaymentFlow('direct');

        if (typeof goSell === 'undefined') {
            
            if (!tap_publishable_key) {
                this._displayErrorDialog(_t("Configuration Error"), _t("The publishable key for Tap is not configured."));
                return;
            }

            await loadJS("https://goSellJSLib.b-cdn.net/v2.0.0/js/gosell.js");
            // await loadJS("/payment_tap/static/src/js/config.js")
            // await loadCSS('https://goSellJSLib.b-cdn.net/v2.0.0/imgs/tap-favicon.ico');
            // await loadCSS('https://goSellJSLib.b-cdn.net/v2.0.0/css/gosell.css');
            
            // // goSell.openPaymentPage()
            // goSell.openLightBox()

            
            this._disableButton(false);
            
            this._initTapForm(tap_publishable_key);
        }
    },

    /**
     * Initialize the Tap goSellElements form.
     */
    _initTapForm(publishableKey) {
        
        // Add the event listener only once.
        if (!this.tapEventListenerAdded) {
            window.addEventListener('message', this._handleTapMessage.bind(this), false);
            this.tapEventListenerAdded = true;
        }

        goSell.goSellElements({
            containerID: 'element-container',
            gateway: {
                publicKey: publishableKey,
                language: "en",
                supportedPaymentMethods: "all",
                notifications: 'standard',
                style: {
                    base: {
                        color: '#535353', lineHeight: '18px', fontFamily: 'sans-serif',
                        fontSmoothing: 'antialiased', fontSize: '16px',
                        '::placeholder': { color: 'rgba(0, 0, 0, 0.26)', fontSize:'15px' }
                    },
                    invalid: { 
                        color: 'red',
                        iconColor: "#fa755a",
                     }
                },
                callback: (response) => {
                    if (response.status =="ACTIVE"){
                        this._createCharge(response.id);
                    }
                }
            }
        });
    },

    /**
     * Handle messages posted from the Tap iframe, specifically for validation errors.
     */
    _handleTapMessage(event) {
        if (event.origin !== "https://secure.gosell.io") {
            return; // Ignore messages from unknown origins
        }

        // console.log(event.data)
        
        // Based on observation, validation errors are sent with a 'type' property.
        if (event.data && (event.data.code == 403 || event.data.code == 400)) {
            this._disableButton(false); // Re-enable the button on validation failure
        }
        else if(event.data && event.data.code == 200){
            this._enableButton(false);
        }
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


        this.paymentContext.reference = processingValues.reference;


        setTimeout(()=>{
            this._enableButton(true);
            this._displayErrorDialog(_t("Server Error"),("Request Timeout, Please check Card details."));
            return;
        }, 15000)


        goSell.submit();
            
    },

    // async _initiatePaymentFlow(providerCode, paymentOptionId, paymentMethodCode, flow) {
    //     if (providerCode !== 'tap' ) {
    //         await this._super(...arguments); 
    //         return;
    //     }
       

    //     const _super = this._super.bind(this);

    //     // goSell.submit();

    //     return await _super(...arguments);
       
        
    // },
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
                this._enableButton(true);
                this._displayErrorDialog(_t("Server Error"), response.error || _t("An unknown error occurred."));
                
            }
        } catch (error) {
            this._enableButton(true);
            this._displayErrorDialog(_t("Technical Error"), _t("An error occurred while creating the charge."));
        }
    },


});

// console.log("here")
//  window.addEventListener('message', function(event) {
            
//             if (event.origin !== "https://secure.gosell.io") {
//                 return; // Ignore messages from unknown origins
//             }

            


//         }, false);

