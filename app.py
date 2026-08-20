"""Aichya Haatche — Homemade Sweets & Namkins E-Commerce Platform."""

import os
import sqlite3
from datetime import datetime
from functools import wraps

from flask import (
    Flask,
    flash,
    g,
    jsonify,
    redirect,
    render_template,
    request,
    session,
    url_for,
)
from flask_login import LoginManager, UserMixin, current_user, login_required, login_user, logout_user
from werkzeug.security import check_password_hash, generate_password_hash

app = Flask(__name__)
app.config["SECRET_KEY"] = "aichya-haatche-secret-key-2026"
app.config["DATABASE"] = os.path.join(app.instance_path, "aichya_haatche.db")

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"
login_manager.login_message_category = "info"


# ---------------------------------------------------------------------------
# Database helpers
# ---------------------------------------------------------------------------

def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(app.config["DATABASE"])
        g.db.row_factory = sqlite3.Row
        g.db.execute("PRAGMA foreign_keys = ON")
    return g.db


@app.teardown_appcontext
def close_db(_exc):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db():
    os.makedirs(app.instance_path, exist_ok=True)
    db = get_db()
    db.executescript(
        """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            is_admin INTEGER DEFAULT 0,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            description TEXT NOT NULL,
            price REAL NOT NULL,
            stock INTEGER NOT NULL DEFAULT 0,
            category TEXT NOT NULL,
            image_url TEXT NOT NULL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS reviews (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            product_id INTEGER NOT NULL,
            rating INTEGER NOT NULL CHECK(rating >= 1 AND rating <= 5),
            comment TEXT NOT NULL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
            FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            customer_name TEXT NOT NULL,
            customer_email TEXT NOT NULL,
            customer_phone TEXT NOT NULL,
            shipping_address TEXT NOT NULL,
            total REAL NOT NULL,
            status TEXT DEFAULT 'confirmed',
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL
        );

        CREATE TABLE IF NOT EXISTS order_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_id INTEGER NOT NULL,
            product_id INTEGER NOT NULL,
            product_name TEXT NOT NULL,
            quantity INTEGER NOT NULL,
            price REAL NOT NULL,
            FOREIGN KEY (order_id) REFERENCES orders(id) ON DELETE CASCADE,
            FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE SET NULL
        );
        """
    )
    db.commit()
    seed_database(db)
    update_product_images(db)


PRODUCT_IMAGE_UPDATES = {
    "Poha Chivda": "https://upload.wikimedia.org/wikipedia/commons/3/3f/Bowl_of_Chivda.jpg",
    "Chakali": "https://upload.wikimedia.org/wikipedia/commons/8/8d/Chakali.JPG",
    "Bhujia": "https://upload.wikimedia.org/wikipedia/commons/e/eb/Crispy_Sev.jpg",
}


def update_product_images(db):
    """Keep product photos accurate when image URLs are corrected."""
    for name, url in PRODUCT_IMAGE_UPDATES.items():
        db.execute("UPDATE products SET image_url = ? WHERE name = ?", (url, name))
    db.commit()


def seed_database(db):
    if db.execute("SELECT COUNT(*) FROM products").fetchone()[0] > 0:
        return

    admins = [
        ("admin1", "admin1@aichyahaatche.com", "admin123"),
        ("admin2", "admin2@aichyahaatche.com", "sweets2024"),
        ("mataji", "mataji@aichyahaatche.com", "aai@123"),
    ]
    for username, email, password in admins:
        db.execute(
            "INSERT INTO users (username, email, password_hash, is_admin) VALUES (?, ?, ?, 1)",
            (username, email, generate_password_hash(password)),
        )

    demo_users = [
        ("priya_sh", "priya@example.com", "user123"),
        ("rahul_p", "rahul@example.com", "user123"),
        ("anita_d", "anita@example.com", "user123"),
    ]
    for username, email, password in demo_users:
        db.execute(
            "INSERT INTO users (username, email, password_hash, is_admin) VALUES (?, ?, ?, 0)",
            (username, email, generate_password_hash(password)),
        )

    products = [
        {
            "name": "Boondi Laddo",
            "description": "Classic golden boondi laddoos bound with aromatic ghee and cardamom. Each bite melts with the warmth of a mother's kitchen.",
            "price": 320,
            "stock": 45,
            "category": "sweets",
            "image_url": "https://upload.wikimedia.org/wikipedia/commons/8/81/A_view_of_Laddu.JPG",
        },
        {
            "name": "Motichoor Laddo",
            "description": "Tiny pearl-like boondi pearls rolled into soft, fragrant laddoos. A festive favourite made fresh every morning.",
            "price": 350,
            "stock": 38,
            "category": "sweets",
            "image_url": "https://upload.wikimedia.org/wikipedia/commons/a/a7/Motichoor_Ladoo.png",
        },
        {
            "name": "Besan Laddo",
            "description": "Roasted chickpea flour laddoos with rich desi ghee and a hint of nutmeg. Wholesome, nutty, and deeply satisfying.",
            "price": 280,
            "stock": 52,
            "category": "sweets",
            "image_url": "https://upload.wikimedia.org/wikipedia/commons/5/58/Besan_laddu_photo.JPG",
        },
        {
            "name": "Karanji",
            "description": "Crisp semolina shells filled with sweet coconut, jaggery, and poppy seeds. A Diwali classic from Maharashtra.",
            "price": 420,
            "stock": 30,
            "category": "sweets",
            "image_url": "https://upload.wikimedia.org/wikipedia/commons/5/5a/Karanji.jpg",
        },
        {
            "name": "Moong Dal Barfi",
            "description": "Silky smooth barfi made from slow-cooked moong dal, khoya, and saffron. Melt-in-mouth luxury in every square.",
            "price": 480,
            "stock": 25,
            "category": "sweets",
            "image_url": "https://upload.wikimedia.org/wikipedia/commons/0/00/Moong_Daal_Barfi.jpg",
        },
        {
            "name": "Chikhalwali",
            "description": "Traditional Maharashtrian layered sweet with flaky texture and rich ghee aroma. Hand-rolled with generations of love.",
            "price": 360,
            "stock": 20,
            "category": "sweets",
            "image_url": "https://upload.wikimedia.org/wikipedia/commons/6/63/Choorma_ladoo.jpg",
        },
        {
            "name": "Gur Wale Laddo",
            "description": "Whole wheat and jaggery laddoos — earthy, wholesome, and naturally sweet. Perfect with evening chai.",
            "price": 240,
            "stock": 40,
            "category": "sweets",
            "image_url": "https://upload.wikimedia.org/wikipedia/commons/2/29/Gur_wale_laddoo.png",
        },
        {
            "name": "Rava Laddo",
            "description": "Semolina laddoos roasted to golden perfection with cashews and raisins. Light, fragrant, and festive.",
            "price": 260,
            "stock": 35,
            "category": "sweets",
            "image_url": "https://upload.wikimedia.org/wikipedia/commons/f/f9/Rava_laddu.jpg",
        },
        {
            "name": "Poha Chivda",
            "description": "Crispy flattened rice tossed with peanuts, curry leaves, and spices. The ultimate Maharashtrian tea-time snack.",
            "price": 180,
            "stock": 60,
            "category": "namkins",
            "image_url": "https://upload.wikimedia.org/wikipedia/commons/3/3f/Bowl_of_Chivda.jpg",
        },
        {
            "name": "Chakali",
            "description": "Spiral-shaped rice flour snacks, deep-fried to crunchy perfection. A mandatory Diwali treat in every Maharashtrian home.",
            "price": 220,
            "stock": 55,
            "category": "namkins",
            "image_url": "https://upload.wikimedia.org/wikipedia/commons/8/8d/Chakali.JPG",
        },
        {
            "name": "Murukku",
            "description": "South Indian-style murukku with a crisp, intricate pattern. Made with rice and urad dal in the traditional 4:1 ratio.",
            "price": 200,
            "stock": 48,
            "category": "namkins",
            "image_url": "https://upload.wikimedia.org/wikipedia/commons/2/26/Murukku_or_Chakli.jpg",
        },
        {
            "name": "Bhujia",
            "description": "Fine, crispy gram flour sev seasoned with black salt and ajwain. Irresistibly light and savoury.",
            "price": 160,
            "stock": 70,
            "category": "namkins",
            "image_url": "https://upload.wikimedia.org/wikipedia/commons/e/eb/Crispy_Sev.jpg",
        },
        {
            "name": "Shankarpali",
            "description": "Diamond-shaped sweet-and-savoury bites — crisp outside, tender inside. A beloved snack across Maharashtra.",
            "price": 190,
            "stock": 42,
            "category": "namkins",
            "image_url": "https://upload.wikimedia.org/wikipedia/commons/7/73/Shankarpali.jpg",
        },
        {
            "name": "Diwali Mix",
            "description": "A curated assortment of murukku, laddu, and ribbon pakoda — the complete festive platter in one box.",
            "price": 550,
            "stock": 15,
            "category": "namkins",
            "image_url": "https://upload.wikimedia.org/wikipedia/commons/c/c8/Diwali_Sweets_and_Snacks.png",
        },
    ]

    for p in products:
        db.execute(
            """INSERT INTO products (name, description, price, stock, category, image_url)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (p["name"], p["description"], p["price"], p["stock"], p["category"], p["image_url"]),
        )

    reviews = [
        (4, 1, 5, "Absolutely divine! Tastes exactly like my grandmother's boondi laddoos."),
        (5, 1, 4, "Fresh and perfectly sweet. Will order again for Diwali."),
        (4, 2, 5, "The motichoor laddoos are so soft and fragrant. Best I've had online."),
        (6, 3, 5, "Rich ghee flavour in every besan laddo. Highly recommended!"),
        (4, 4, 5, "Karanji filling was perfect — coconut and jaggery balance is spot on."),
        (5, 5, 4, "Barfi was fresh and not overly sweet. Great quality."),
        (4, 9, 5, "This chivda reminds me of Pune street food festivals. Crispy perfection!"),
        (6, 10, 5, "Chakali was so crunchy and fresh. Arrived intact despite shipping."),
        (5, 11, 4, "Authentic murukku taste. My family finished the whole batch in one sitting."),
        (4, 12, 5, "Light, crispy bhujia — perfect with chai every evening."),
    ]
    for user_id, product_id, rating, comment in reviews:
        db.execute(
            "INSERT INTO reviews (user_id, product_id, rating, comment) VALUES (?, ?, ?, ?)",
            (user_id, product_id, rating, comment),
        )

    db.commit()


with app.app_context():
    init_db()


# ---------------------------------------------------------------------------
# User model
# ---------------------------------------------------------------------------

class User(UserMixin):
    def __init__(self, id, username, email, password_hash, is_admin):
        self.id = id
        self.username = username
        self.email = email
        self.password_hash = password_hash
        self.is_admin = bool(is_admin)


@login_manager.user_loader
def load_user(user_id):
    row = get_db().execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
    if row:
        return User(row["id"], row["username"], row["email"], row["password_hash"], row["is_admin"])
    return None


def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            flash("Admin access required.", "error")
            return redirect(url_for("admin_login"))
        return f(*args, **kwargs)
    return decorated


# ---------------------------------------------------------------------------
# Cart helpers
# ---------------------------------------------------------------------------

def get_cart():
    return session.setdefault("cart", {})


def cart_count():
    cart = get_cart()
    return sum(item["qty"] for item in cart.values())


def cart_total():
    cart = get_cart()
    return sum(item["price"] * item["qty"] for item in cart.values())


@app.context_processor
def inject_globals():
    return {"cart_count": cart_count(), "brand_name": "आईच्या हातचे", "brand_tagline": "From Mother's Hands"}


# ---------------------------------------------------------------------------
# Product helpers
# ---------------------------------------------------------------------------

def get_product_rating(product_id):
    row = get_db().execute(
        "SELECT AVG(rating) as avg_rating, COUNT(*) as count FROM reviews WHERE product_id = ?",
        (product_id,),
    ).fetchone()
    return round(row["avg_rating"] or 0, 1), row["count"]


def enrich_product(product):
    avg, count = get_product_rating(product["id"])
    product = dict(product)
    product["avg_rating"] = avg
    product["review_count"] = count
    return product


# ---------------------------------------------------------------------------
# Public routes
# ---------------------------------------------------------------------------

@app.route("/")
def index():
    db = get_db()
    featured = db.execute(
        "SELECT * FROM products ORDER BY RANDOM() LIMIT 6"
    ).fetchall()
    sweets_count = db.execute("SELECT COUNT(*) FROM products WHERE category='sweets'").fetchone()[0]
    namkins_count = db.execute("SELECT COUNT(*) FROM products WHERE category='namkins'").fetchone()[0]
    return render_template(
        "index.html",
        featured=[enrich_product(p) for p in featured],
        sweets_count=sweets_count,
        namkins_count=namkins_count,
    )


@app.route("/shop")
def shop():
    category = request.args.get("category", "")
    db = get_db()
    if category in ("sweets", "namkins"):
        products = db.execute(
            "SELECT * FROM products WHERE category = ? ORDER BY name", (category,)
        ).fetchall()
    else:
        products = db.execute("SELECT * FROM products ORDER BY category, name").fetchall()
    return render_template(
        "shop.html",
        products=[enrich_product(p) for p in products],
        active_category=category,
    )


@app.route("/product/<int:product_id>")
def product_detail(product_id):
    db = get_db()
    product = db.execute("SELECT * FROM products WHERE id = ?", (product_id,)).fetchone()
    if not product:
        flash("Product not found.", "error")
        return redirect(url_for("shop"))
    reviews = db.execute(
        """SELECT r.*, u.username FROM reviews r
           JOIN users u ON r.user_id = u.id
           WHERE r.product_id = ? ORDER BY r.created_at DESC""",
        (product_id,),
    ).fetchall()
    product = enrich_product(product)
    return render_template("product.html", product=product, reviews=reviews)


@app.route("/product/<int:product_id>/review", methods=["POST"])
@login_required
def add_review(product_id):
    rating = int(request.form.get("rating", 0))
    comment = request.form.get("comment", "").strip()
    if rating < 1 or rating > 5 or not comment:
        flash("Please provide a valid rating (1-5) and comment.", "error")
        return redirect(url_for("product_detail", product_id=product_id))

    get_db().execute(
        "INSERT INTO reviews (user_id, product_id, rating, comment) VALUES (?, ?, ?, ?)",
        (current_user.id, product_id, rating, comment),
    )
    get_db().commit()
    flash("Thank you for your review!", "success")
    return redirect(url_for("product_detail", product_id=product_id))


@app.route("/cart/add/<int:product_id>", methods=["POST"])
def add_to_cart(product_id):
    db = get_db()
    product = db.execute("SELECT * FROM products WHERE id = ?", (product_id,)).fetchone()
    if not product:
        flash("Product not found.", "error")
        return redirect(url_for("shop"))
    if product["stock"] <= 0:
        flash(f"{product['name']} is out of stock.", "error")
        return redirect(url_for("product_detail", product_id=product_id))

    qty = max(1, int(request.form.get("quantity", 1)))
    cart = get_cart()
    key = str(product_id)
    current_qty = cart.get(key, {}).get("qty", 0)
    if current_qty + qty > product["stock"]:
        flash(f"Only {product['stock']} units available.", "error")
        return redirect(url_for("product_detail", product_id=product_id))

    cart[key] = {
        "id": product["id"],
        "name": product["name"],
        "price": product["price"],
        "qty": current_qty + qty,
        "image_url": product["image_url"],
    }
    session["cart"] = cart
    session.modified = True
    flash(f"{product['name']} added to cart!", "success")
    next_page = request.form.get("next") or request.referrer or url_for("shop")
    return redirect(next_page)


@app.route("/cart")
def cart():
    cart = get_cart()
    items = []
    for key, item in cart.items():
        product = get_db().execute("SELECT stock FROM products WHERE id = ?", (item["id"],)).fetchone()
        item["stock"] = product["stock"] if product else 0
        items.append(item)
    return render_template("cart.html", items=items, total=cart_total())


@app.route("/cart/update", methods=["POST"])
def update_cart():
    cart = get_cart()
    for key in list(cart.keys()):
        qty = int(request.form.get(f"qty_{key}", 0))
        if qty <= 0:
            del cart[key]
        else:
            product = get_db().execute("SELECT stock FROM products WHERE id = ?", (cart[key]["id"],)).fetchone()
            if product:
                cart[key]["qty"] = min(qty, product["stock"])
    session["cart"] = cart
    session.modified = True
    return redirect(url_for("cart"))


@app.route("/cart/remove/<int:product_id>")
def remove_from_cart(product_id):
    cart = get_cart()
    cart.pop(str(product_id), None)
    session["cart"] = cart
    session.modified = True
    flash("Item removed from cart.", "info")
    return redirect(url_for("cart"))


@app.route("/checkout", methods=["GET", "POST"])
def checkout():
    cart = get_cart()
    if not cart:
        flash("Your cart is empty.", "info")
        return redirect(url_for("shop"))

    items = list(cart.values())
    total = cart_total()

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip()
        phone = request.form.get("phone", "").strip()
        address = request.form.get("address", "").strip()

        if not all([name, email, phone, address]):
            flash("Please fill in all fields.", "error")
            return render_template("checkout.html", items=items, total=total)

        db = get_db()
        for item in items:
            product = db.execute("SELECT stock FROM products WHERE id = ?", (item["id"],)).fetchone()
            if not product or product["stock"] < item["qty"]:
                flash(f"Insufficient stock for {item['name']}.", "error")
                return redirect(url_for("cart"))

        user_id = current_user.id if current_user.is_authenticated else None
        cursor = db.execute(
            """INSERT INTO orders (user_id, customer_name, customer_email, customer_phone, shipping_address, total)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (user_id, name, email, phone, address, total),
        )
        order_id = cursor.lastrowid

        for item in items:
            db.execute(
                """INSERT INTO order_items (order_id, product_id, product_name, quantity, price)
                   VALUES (?, ?, ?, ?, ?)""",
                (order_id, item["id"], item["name"], item["qty"], item["price"]),
            )
            db.execute(
                "UPDATE products SET stock = stock - ? WHERE id = ?",
                (item["qty"], item["id"]),
            )

        db.commit()
        session["cart"] = {}
        session.modified = True
        return render_template("checkout_success.html", order_id=order_id, total=total, name=name)

    return render_template("checkout.html", items=items, total=total)


# ---------------------------------------------------------------------------
# Auth routes
# ---------------------------------------------------------------------------

@app.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("index"))
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "")
        confirm = request.form.get("confirm", "")

        if not username or not email or not password:
            flash("All fields are required.", "error")
        elif password != confirm:
            flash("Passwords do not match.", "error")
        elif len(password) < 6:
            flash("Password must be at least 6 characters.", "error")
        else:
            db = get_db()
            existing = db.execute(
                "SELECT id FROM users WHERE username = ? OR email = ?", (username, email)
            ).fetchone()
            if existing:
                flash("Username or email already registered.", "error")
            else:
                db.execute(
                    "INSERT INTO users (username, email, password_hash) VALUES (?, ?, ?)",
                    (username, email, generate_password_hash(password)),
                )
                db.commit()
                flash("Registration successful! Please log in.", "success")
                return redirect(url_for("login"))
    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("index"))
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        row = get_db().execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()
        if row and check_password_hash(row["password_hash"], password):
            user = User(row["id"], row["username"], row["email"], row["password_hash"], row["is_admin"])
            login_user(user)
            flash(f"Welcome back, {username}!", "success")
            next_page = request.args.get("next")
            if row["is_admin"]:
                return redirect(next_page or url_for("admin_dashboard"))
            return redirect(next_page or url_for("index"))
        flash("Invalid username or password.", "error")
    return render_template("login.html")


@app.route("/logout")
def logout():
    logout_user()
    flash("You have been logged out.", "info")
    return redirect(url_for("index"))


@app.route("/account")
def account():
    if not current_user.is_authenticated:
        return redirect(url_for("login"))
    orders = get_db().execute(
        """SELECT * FROM orders WHERE user_id = ? OR customer_email = ?
           ORDER BY created_at DESC""",
        (current_user.id, current_user.email),
    ).fetchall()
    return render_template("account.html", orders=orders)


# ---------------------------------------------------------------------------
# Admin routes
# ---------------------------------------------------------------------------

@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    if current_user.is_authenticated and current_user.is_admin:
        return redirect(url_for("admin_dashboard"))
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        row = get_db().execute(
            "SELECT * FROM users WHERE username = ? AND is_admin = 1", (username,)
        ).fetchone()
        if row and check_password_hash(row["password_hash"], password):
            user = User(row["id"], row["username"], row["email"], row["password_hash"], row["is_admin"])
            login_user(user)
            flash(f"Welcome, Admin {username}!", "success")
            return redirect(url_for("admin_dashboard"))
        flash("Invalid admin credentials.", "error")
    return render_template("admin/login.html")


@app.route("/admin")
@app.route("/admin/dashboard")
@admin_required
def admin_dashboard():
    db = get_db()
    stats = {
        "products": db.execute("SELECT COUNT(*) FROM products").fetchone()[0],
        "orders": db.execute("SELECT COUNT(*) FROM orders").fetchone()[0],
        "reviews": db.execute("SELECT COUNT(*) FROM reviews").fetchone()[0],
        "low_stock": db.execute("SELECT COUNT(*) FROM products WHERE stock < 10").fetchone()[0],
    }
    recent_orders = db.execute(
        "SELECT * FROM orders ORDER BY created_at DESC LIMIT 5"
    ).fetchall()
    products = db.execute("SELECT * FROM products ORDER BY category, name").fetchall()
    return render_template("admin/dashboard.html", stats=stats, recent_orders=recent_orders, products=products)


@app.route("/admin/products")
@admin_required
def admin_products():
    products = get_db().execute("SELECT * FROM products ORDER BY category, name").fetchall()
    return render_template("admin/products.html", products=products)


@app.route("/admin/products/add", methods=["GET", "POST"])
@admin_required
def admin_add_product():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        description = request.form.get("description", "").strip()
        price = float(request.form.get("price", 0))
        stock = int(request.form.get("stock", 0))
        category = request.form.get("category", "sweets")
        image_url = request.form.get("image_url", "").strip()

        if not all([name, description, image_url]) or price <= 0:
            flash("Please fill in all required fields.", "error")
        else:
            get_db().execute(
                """INSERT INTO products (name, description, price, stock, category, image_url)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (name, description, price, stock, category, image_url),
            )
            get_db().commit()
            flash(f"Product '{name}' added successfully!", "success")
            return redirect(url_for("admin_products"))
    return render_template("admin/product_form.html", product=None)


@app.route("/admin/products/<int:product_id>/edit", methods=["GET", "POST"])
@admin_required
def admin_edit_product(product_id):
    db = get_db()
    product = db.execute("SELECT * FROM products WHERE id = ?", (product_id,)).fetchone()
    if not product:
        flash("Product not found.", "error")
        return redirect(url_for("admin_products"))

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        description = request.form.get("description", "").strip()
        price = float(request.form.get("price", 0))
        stock = int(request.form.get("stock", 0))
        category = request.form.get("category", "sweets")
        image_url = request.form.get("image_url", "").strip()

        if not all([name, description, image_url]) or price <= 0:
            flash("Please fill in all required fields.", "error")
        else:
            db.execute(
                """UPDATE products SET name=?, description=?, price=?, stock=?, category=?, image_url=?
                   WHERE id=?""",
                (name, description, price, stock, category, image_url, product_id),
            )
            db.commit()
            flash(f"Product '{name}' updated!", "success")
            return redirect(url_for("admin_products"))
    return render_template("admin/product_form.html", product=product)


@app.route("/admin/products/<int:product_id>/delete", methods=["POST"])
@admin_required
def admin_delete_product(product_id):
    db = get_db()
    product = db.execute("SELECT name FROM products WHERE id = ?", (product_id,)).fetchone()
    if product:
        db.execute("DELETE FROM products WHERE id = ?", (product_id,))
        db.commit()
        flash(f"Product '{product['name']}' deleted.", "info")
    return redirect(url_for("admin_products"))


@app.route("/admin/stock/<int:product_id>", methods=["POST"])
@admin_required
def admin_update_stock(product_id):
    stock = int(request.form.get("stock", 0))
    db = get_db()
    db.execute("UPDATE products SET stock = ? WHERE id = ?", (stock, product_id))
    db.commit()
    if request.headers.get("X-Requested-With") == "XMLHttpRequest":
        return jsonify({"success": True, "stock": stock})
    flash("Stock updated.", "success")
    return redirect(url_for("admin_dashboard"))


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
