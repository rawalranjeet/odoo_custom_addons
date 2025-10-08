# 🔒 Odoo Tap Payment Integration

An Odoo add-on that integrates **Tap Payments** with Odoo, allowing you to accept online payments via Tap in your eCommerce.
Tap is a secure and developer-friendly payment gateway serving businesses in the MENA region.

---

## 📦 Module Information  

| Key          | Value                                    |
|--------------|------------------------------------------|
| **Name**     | Tap Payment                              |
| **Version**  | 18.0.1.0.0                               |
| **Author**   | CodeTrade India Pvt. Ltd.	             |
| **Category** | Accounting/Payment Providers             |
| **License**  | LGPL-3                                   |
| **Odoo**     | v18.0                                    |
| **support**  | https://www.codetrade.io                 |

---

## 📖 Overview  

Managing online payments securely and efficiently is crucial for any eCommerce business.
With **Tap Payment Gateway** for Odoo eCommerce, you can:

- Seamlessly integrate Tap Payments into your Odoo website checkout.
- Accept payments via credit/debit cards, Apple Pay, Mada, and other Tap-supported methods.
- Ensure secure transactions with real-time status updates and error handling.
- Offer customers a smooth and localized payment experience across the Gulf region.
- Automatically sync payment data with Odoo Sales, Invoices, and Accounting modules.  

---

⚡ Key Features

- 💳 Multiple Payment Methods – Accept cards, Apple Pay, Mada, and more via Tap.
- 🔐 Secure Payment Processing – PCI-compliant integration with encrypted data handling.
- 🔄 Real-Time Payment Sync – Instantly update payment status in Sales and Invoices.
- 🛒 Seamless Checkout Integration – Embedded smoothly into Odoo website flow.
- 🌍 GCC-Ready Experience – Optimized for customers in Saudi Arabia, UAE, Kuwait, and beyond.
- ⚙️ Easy Setup & Configuration – Install, connect, and go live in minutes. 

---

## 🎯 Use Cases  

- When a customer checks out via the website, they will see **Tap** as a payment option.
- Upon choosing Tap, they are redirected to the Tap payment page.
- After payment, they return to Odoo, and the transaction is validated automatically. 

---

## 🛠️ Installation

1. Download or clone the repository into your Odoo `addons` folder

2. Restart Odoo server:

```bash
./odoo-bin -c odoo.conf -u ct_payment_tap
```

3. Activate the module from the **Apps** menu.

---

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
├── data/
│   ├── payment_method_data.xml
│   └── payment_provider_data.xml
│
├── models/
│   ├── __init__.py
│   ├── payment_provider.py
│   ├── payment_token.py
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
│
├── views/
│   ├── payment_provider_views.xml
│   └── payment_tap_template.xml
```

---

## 📜 License

This module is licensed under the **LGPL-3 License**.

## ⚡ This version is **ready-to-use on Odoo 18**