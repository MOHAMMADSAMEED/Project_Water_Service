# 💧 Water Filter — Delivery & Service App


## 📁 Folder Structure

```
mulla_water/
├── app.py                  ← Main Flask application
├── init_db.py              ← Standalone DB setup script
├── requirements.txt        ← Python dependencies
├── mulla_water.db          ← SQLite database (auto-created)
├── static/
│   ├── css/
│   │   └── style.css       ← All styles (Islamic green theme)
│   ├── js/
│   │   └── main.js         ← Frontend interactions
│   └── images/             ← Product images (SVGs)
└── templates/
    ├── base.html            ← Master layout with nav & footer
    ├── index.html           ← Homepage with hero & products
    ├── login.html           ← Login page
    ├── register.html        ← Registration page
    ├── products.html        ← Products listing
    ├── product_detail.html  ← Single product detail
    ├── cart.html            ← Shopping cart
    ├── checkout.html        ← Checkout & delivery scheduling
    ├── order_success.html   ← Order confirmation + WhatsApp
    ├── my_orders.html       ← Customer order history
    ├── order_detail.html    ← Single order detail
    ├── admin/
    │   ├── dashboard.html   ← Admin control panel
    │   └── orders.html      ← All orders view
    └── owner/
        └── dashboard.html   ← Owner order management
```

---




## 🌟 Feature Summary

| Feature               | Status |
|-----------------------|--------|
| Customer Registration | ✅     |
| Role-Based Login      | ✅     |
| Product Catalog       | ✅     |
| Shopping Cart         | ✅     |
| Checkout + Scheduling | ✅     |
| WhatsApp Notification | ✅     |
| Order Tracking        | ✅     |
| Admin Panel           | ✅     |
| Owner Panel           | ✅     |
| Cash on Delivery      | ✅     |
| UPI/Card (stub)       | 🔜     |
| Islamic UI Theme      | ✅     |
| Mobile Responsive     | ✅     |

---

## 📱 WhatsApp Integration

When a customer places an order, the success page shows a **"Send WhatsApp to Owner"** button. This uses the `wa.me` API — clicking it opens WhatsApp with a pre-filled message containing:
- Customer name
- Products ordered
- Quantity & total price
- Delivery date & time
- Delivery address

To update the owner's phone number, edit the `owner` user in the database or via the Admin panel.

---

## 💳 Adding a Real Payment Gateway

The checkout form has `payment_method` field and the orders table has `payment_status`. To add Razorpay/Stripe:

1. Add your API keys to `app.py`
2. In `/checkout` POST route, after order creation, call the payment API
3. Add a webhook route `/payment/webhook` to update `payment_status`
4. Update the checkout template with the payment SDK

