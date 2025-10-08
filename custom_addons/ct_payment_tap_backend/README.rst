# 🔒 Odoo Tap Backend Payment Integration

An Odoo add-on that integrates **Tap Payments** with the Odoo backend, allowing you to process payments for Sales Orders and Invoices directly. Tap is a secure and developer-friendly payment gateway serving businesses in the MENA region.

-----

## 📦 Module Information  

| Key          | Value                                    |
|--------------|------------------------------------------|
| **Name**     | Backend Payment: Tap                     |
| **Version**  | 18.0.1.0.1                               |
| **Author**   | CodeTrade India Pvt. Ltd.	             |
| **Category** | Accounting/Payment Providers             |
| **License**  | LGPL-3                                   |
| **Odoo**     | v18.0                                    |
| **support**  | https://www.codetrade.io                 |

---

## 📖 Overview

This module extends the Tap Payment integration to the Odoo backend, enabling your staff to process payments manually and securely. It is ideal for handling Mail Order/Telephone Order (MOTO) transactions or for when customers prefer to pay over the phone. A key feature is the ability to save customer payment details as secure tokens for fast and convenient future payments.

-----

⚡ **Key Features**

  - 💳 **Backend Payment Processing** – Manually process customer payments directly from Sales Orders or Invoices in the Odoo backend.
  - 🔐 **Secure Payment Tokenization** – Save customer card details securely as a Tap token for future use.
  - 🔄 **Reuse Saved Cards** – Charge a customer's saved card with a single click, eliminating the need to re-enter details.
  - 📈 **Real-Time Payment Sync** – Instantly update the payment status on invoices and sales orders after a successful backend transaction.
  - ⚙️ **Seamless User Experience** – A straightforward and integrated payment flow for your backend users.
  - 🛡️ **PCI-Compliant Security** – All transactions are handled securely via Tap's encrypted systems, ensuring data protection.

-----

## 🎯 Use Cases

  - A sales agent finalizes an order with a customer over the phone.
  - From the Sales Order or Invoice in the Odoo backend, the agent initiates a payment.
  - They choose **Tap** as the payment method.
  - The agent enters the customer's card details into the secure Tap form.
  - They can select an option to "Save Card for Future Use," which creates a secure payment token.
  - For subsequent orders from the same customer, the agent can simply select the saved token to process the payment instantly.

-----

## 🛠️ Installation

1.  Download or clone the repository into your Odoo `addons` folder.
2.  Ensure the base module `ct_payment_tap` is also installed.
3.  Restart the Odoo server:
    ```bash
    ./odoo-bin -c odoo.conf -u ct_payment_tap_backend
    ```
4.  Activate the module from the **Apps** menu.

-----

## 📂 Module Structure

```
ct_payment_tap/
│── __manifest__.py
│── __init__.py
│
├── controllers/
│   ├── __init__.py
│   └── main.py
│
├── models/
│   ├── __init__.py
│   ├── payment_backend_invoice.py
│   └── payment_transaction.py
│
├── static/
│   └── description/
│       ├── t1.png
│       ├── t2.png
│       ├── t3.png
│       ├── t4.png
│       ├── t5.png
│       ├── t6.png
│       ├── t7.png
│   └── img/
│       ├── tap.png
│
├── views/
│   └── account_payment_register.xml
```

-----

## 📜 License

This module is licensed under the **LGPL-3 License**.

## ⚡ This version is **ready-to-use on Odoo 18**