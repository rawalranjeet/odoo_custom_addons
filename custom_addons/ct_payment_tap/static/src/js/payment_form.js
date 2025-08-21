/** @odoo-module **/

import { _t } from '@web/core/l10n/translation';
import { loadJS, loadCSS } from '@web/core/assets';
import paymentForm from '@payment/js/payment_form';
import { rpc } from "@web/core/network/rpc";


paymentForm.include({
    tapEventListenerAdded: false,

    async _selectPaymentOption(ev){
        const paymentMethodCode = ev.target.dataset.paymentMethodCode
        await this._super(...arguments)

        if (paymentMethodCode === 'tap_direct'){
            this._disableButton()
        }
    },

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
        // const tap_payment_flow_type = tapInlineFormValues.tap_payment_flow_type
        

        if (paymentMethodCode === 'tap_redirect'){
            return;
        }
        
        this._setPaymentFlow('direct');
        

        if (typeof goSell === 'undefined') {
            
            if (!tap_publishable_key) {
                this._displayErrorDialog(_t("Configuration Error"), _t("The publishable key for Tap is not configured."));
                return;
            }

            
            // Load required js and css for Tap Payments
            await loadJS("https://goSellJSLib.b-cdn.net/v2.0.0/js/gosell.js");
            await loadCSS('https://goSellJSLib.b-cdn.net/v2.0.0/imgs/tap-favicon.ico');
            await loadCSS('https://goSellJSLib.b-cdn.net/v2.0.0/css/gosell.css');
            
            

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
                supportedPaymentMethods: 'all',
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

        if (event.data && (event.data.code == 403 || event.data.error_interactive)) {
            this._disableButton(false); 
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
                this._enableButton(true);
                this._displayErrorDialog(_t("Server Error"), response.error || _t("An unknown error occurred."));
                
            }
        } catch (error) {
            this._enableButton(true);
            this._displayErrorDialog(_t("Technical Error"), _t("An error occurred while creating the charge."));
        }
    },


});



// #=== DOM MANIPULATION ===#

    // async _change_flow(providerId, providerCode, paymentOptionId, paymentMethodCode, flow){
    //     const radios = document.querySelectorAll('input[name="payment_tap_flow_type_input"]');
    //     radios.forEach(radio => {
    //         radio.addEventListener('change', async() => {
    //             const selectedRadio = document.querySelector('input[name="payment_tap_flow_type_input"]:checked');
                
    //             // console.log("flow changed")
                

    //             // ----------
               
    //             this._collapseInlineForms();
    //             this._setPaymentFlow(selectedRadio.value);

    //             if (selectedRadio.value === 'redirect'){
    //                 return;
    //             }

    //             const paymentradio = document.querySelector('input[name="o_payment_radio"]:checked');

    //             // Prepare the inline form of the selected payment option.
    //             const providerId = this._getProviderId(paymentradio);
    //             const providerCode = this._getProviderCode(paymentradio);
    //             const paymentOptionId = this._getPaymentOptionId(paymentradio);
    //             const paymentMethodCode = this._getPaymentMethodCode(paymentradio);
    //             const flow = this._getPaymentFlow(paymentradio);
    //             await this._prepareInlineForm(
    //                 providerId, providerCode, paymentOptionId, paymentMethodCode, flow
    //             );

    //             // Display the prepared inline form if it is not empty.
    //             const inlineForm = this._getInlineForm(paymentradio);
    //             if (inlineForm && inlineForm.children.length > 0) {
    //                 inlineForm.classList.remove('d-none');
    //             }

    //         });
    //     })
    // },

    // async start(){
    //     this._change_flow()
    //     return this._super()
    // },
    

    // async _selectPaymentOption(ev){
    //     const providerCode = ev.target.dataset.providerCode

    //     const payment_tap_flow_type_div = document.getElementById("payment_tap_flow_type")

    //     if (payment_tap_flow_type_div){
    //         if (providerCode === 'tap'){
    //             payment_tap_flow_type_div.style.display = 'block'
    //         }
    //         else{
    //             payment_tap_flow_type_div.style.display = 'none'
    //         }
    //     }

    //     return await this._super(...arguments)
    // },