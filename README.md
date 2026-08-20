# आईच्या हातचे (Aichya Haatche)

**From Mother's Hands** — A complete e-commerce platform for homemade Maharashtrian sweets and namkins.

## Quick Start

No configuration required. Run these two commands:

```bash
pip install -r requirements.txt
python3 app.py
```

Or use the included startup script:

```bash
./run.sh
```

Open **http://localhost:5000** in your browser.

The SQLite database is created automatically on first run with all products, admin accounts, and sample reviews pre-loaded.

## Brand

| | |
|---|---|
| **Marathi Name** | आईच्या हातचे |
| **English** | Aichya Haatche |
| **Tagline** | From Mother's Hands — Homemade with Love |

## Features

- **Product Catalog** — Sweets (laddoos, karanji, barfi, chikhalwali) and Namkins (chivda, chakali, murukku, bhujia)
- **Shopping Cart & Checkout** — Add items, adjust quantities, place orders in ₹ (Indian Rupees)
- **User Reviews** — Rate and review products (1–5 stars with comments)
- **User Authentication** — Register, login, view order history
- **Admin Dashboard** — Real-time stock management, add/edit/delete products
- **3D Animations** — Three.js floating sweets in hero section, CSS 3D tilt on product cards
- **Responsive Design** — Works on desktop, tablet, and mobile

## Demo Accounts

### Admin (Inventory Management)
| Username | Password |
|----------|----------|
| admin1 | admin123 |
| admin2 | sweets2024 |
| mataji | aai@123 |

### Customer (Reviews & Orders)
| Username | Password |
|----------|----------|
| priya_sh | user123 |
| rahul_p | user123 |
| anita_d | user123 |

Or register a new account from the Register page.

## Admin Capabilities

- View dashboard with product, order, and review statistics
- Update product stock in real time from the dashboard
- Add new products with name, description, price (₹), stock, category, and image URL
- Edit existing products
- Delete products
- View recent orders

## Tech Stack

- **Backend:** Python 3 + Flask
- **Database:** SQLite (auto-created at `instance/aichya_haatche.db`)
- **Auth:** Flask-Login with Werkzeug password hashing
- **Frontend:** HTML, CSS, JavaScript
- **3D:** Three.js (CDN)
- **Images:** Wikimedia Commons (verified working URLs)

## Project Structure

```
├── app.py                  # Main Flask application
├── requirements.txt        # Python dependencies
├── instance/               # SQLite database (auto-created)
├── static/
│   ├── css/style.css       # Styles
│   └── js/
│       ├── main.js         # UI interactions & 3D tilt
│       └── three-hero.js   # Three.js hero animation
└── templates/              # Jinja2 HTML templates
    ├── base.html
    ├── index.html
    ├── shop.html
    ├── product.html
    ├── cart.html
    ├── checkout.html
    ├── login.html
    ├── register.html
    ├── account.html
    └── admin/
        ├── login.html
        ├── dashboard.html
        ├── products.html
        └── product_form.html
```

## License

Built for demonstration purposes. Product images sourced from Wikimedia Commons under Creative Commons licenses.
