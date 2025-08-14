/** @odoo-module **/

import { PaymentScreen } from "@point_of_sale/app/screens/payment_screen/payment_screen";
import { PaymentInterface } from "@point_of_sale/app/payment/payment_interface";
import { ErrorPopup } from "@point_of_sale/app/errors/popups/error_popup";
import { QrCodePopup } from "@point_of_sale/app/utils/qr_code_popup/qr_code_popup";
import { patch } from "@web/core/utils/patch";
import { useService } from "@web/core/utils/hooks";
import { register_payment_method } from "@point_of_sale/app/store/pos_store";

class PaymentEFT extends PaymentInterface {
    setup() {
        super.setup();
        this.rpc = useService("rpc");
        this.popup = useService("popup");
    }

    async send_payment_request(cid) {
        const line = this.pos.get_order().get_paymentline(cid);
        line.set_payment_status("pending");

        try {
            const response = await this.rpc("/eft/payment/start", {
                amount: line.amount,
                method_id: line.payment_method.id,
            });

            if (response.error) {
                throw new Error(response.error);
            }

            if (response.qr_code_base64) {
                line.transaction_id = response.transaction_id;
                line.eft_qr_code = response.qr_code_base64;
                return this.waitForConfirmation(line);
            } else {
                throw new Error("No QR code was returned from the server.");
            }
        } catch (error) {
            line.set_payment_status("retry");
            this.popup.add(ErrorPopup, {
                title: "Payment Error",
                body: error.message || "Could not connect to the payment server.",
            });
            return false;
        }
    }

    async waitForConfirmation(line) {
        // This is where the QR code is displayed and we wait for the user action.
        // In a real scenario, you would poll a status endpoint or wait for a webhook.
        const { confirmed } = await this.popup.add(QrCodePopup, {
            title: `Scan to pay with ${line.payment_method.name}`,
            qr_code_data: line.eft_qr_code,
        });

        if (confirmed) {
            // This assumes the cashier manually confirms the payment was received.
            line.set_payment_status("done");
            return true;
        } else {
            // User cancelled the popup.
            line.set_payment_status("retry");
            return false;
        }
    }
}

// Register this payment interface for each enabled terminal type.
const EFT_TERMINALS = ["alipay", "wechat", "fps", "payme", "unionpay"];
for (const terminal of EFT_TERMINALS) {
    register_payment_method(terminal, PaymentEFT);
}

// Patch the payment screen to handle the QR code display logic if needed.
// The current logic uses a popup, which is cleaner.
patch(PaymentScreen.prototype, {
    // This patch can be extended if more complex UI interactions are needed.
});
