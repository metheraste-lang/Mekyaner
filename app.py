import os
import random
import string
from datetime import datetime

from flask import (
    Flask, render_template, request, redirect, url_for,
    session, flash
)
from werkzeug.utils import secure_filename

from db import get_db, init_db

app = Flask(__name__)
app.secret_key = "change-cette-cle-avant-la-mise-en-ligne"  # à remplacer par une vraie clé secrète en production

UPLOAD_FOLDER = os.path.join(app.static_folder, "uploads")
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "webp"}
ADMIN_PASSWORD = "mekyaner2026"  # à changer avant la mise en ligne

CATEGORY_LABELS = {
    "physique": "Produit physique",
    "digital": "Produit digital",
    "formation": "Formation",
}

PAYMENT_METHODS = [
    {"id": "airtel", "label": "Airtel Money", "number": "86752575", "active": True},
    {"id": "moov", "label": "Moov Money", "number": "98587597", "active": True},
    {"id": "mtn", "label": "MTN Money", "number": "Bientôt disponible", "active": False},
    {"id": "orange", "label": "Orange Money", "number": "Bientôt disponible", "active": False},
]


def gen_id(prefix="MK"):
    return prefix + "-" + "".join(random.choices(string.ascii_uppercase + string.digits, k=6))


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def format_fcfa(n):
    return f"{n:,}".replace(",", " ") + " FCFA"


app.jinja_env.filters["fcfa"] = format_fcfa


def get_cart():
    return session.get("cart", [])


def save_cart(cart):
    session["cart"] = cart
    session.modified = True


# ---------- PAGES PUBLIQUES ----------

@app.route("/")
def accueil():
    return render_template("accueil.html", cart_count=cart_count())


@app.route("/catalogue")
def catalogue():
    db = get_db()
    products = db.execute("SELECT * FROM products ORDER BY created_at DESC, id").fetchall()
    db.close()
    filter_type = request.args.get("type", "all")
    return render_template(
        "catalogue.html", products=products, category_labels=CATEGORY_LABELS,
        filter_type=filter_type, cart_count=cart_count()
    )


@app.route("/formations")
def formations():
    db = get_db()
    products = db.execute("SELECT * FROM products WHERE type='formation' ORDER BY created_at DESC").fetchall()
    db.close()
    return render_template("formations.html", products=products, cart_count=cart_count())


@app.route("/apropos")
def apropos():
    return render_template("apropos.html", cart_count=cart_count())


@app.route("/contact")
def contact():
    return render_template("contact.html", cart_count=cart_count())


@app.route("/produit/<product_id>", methods=["GET", "POST"])
def produit(product_id):
    db = get_db()
    product = db.execute("SELECT * FROM products WHERE id=?", (product_id,)).fetchone()

    if not product:
        db.close()
        return render_template("produit.html", product=None, cart_count=cart_count())

    if request.method == "GET":
        db.execute("UPDATE products SET clicks = clicks + 1 WHERE id=?", (product_id,))
        db.commit()

    if request.method == "POST":
        payment_method = request.form.get("payment_method", "airtel")
        order = {
            "id": gen_id(),
            "cart_ref": None,
            "product_id": product["id"],
            "product_name": product["name"],
            "type": product["type"],
            "price": product["price"],
            "customer_name": request.form.get("nom", ""),
            "customer_firstname": request.form.get("prenom", ""),
            "phone": request.form.get("phone", ""),
            "quartier": request.form.get("quartier", ""),
            "payment_method": "livraison" if product["type"] == "physique" else payment_method,
            "proof": "" if product["type"] == "physique" else request.form.get("proof", ""),
            "digital_content": product["digital_content"],
            "status": "a_livrer" if product["type"] == "physique" else "en_attente",
            "created_at": datetime.utcnow().isoformat(),
        }
        db.execute(
            """INSERT INTO orders (id, cart_ref, product_id, product_name, type, price,
               customer_name, customer_firstname, phone, quartier, payment_method, proof,
               digital_content, status, created_at)
               VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            tuple(order.values())
        )
        db.commit()
        db.close()
        return render_template("produit.html", product=product, confirmation=order, cart_count=cart_count())

    db.close()
    return render_template(
        "produit.html", product=product, category_labels=CATEGORY_LABELS,
        payment_methods=PAYMENT_METHODS, cart_count=cart_count()
    )


# ---------- PANIER ----------

def cart_count():
    return sum(item["qty"] for item in get_cart())


@app.route("/panier")
def panier():
    cart = get_cart()
    total = sum(item["price"] * item["qty"] for item in cart)
    physique_total = sum(item["price"] * item["qty"] for item in cart if item["type"] == "physique")
    digital_total = sum(item["price"] * item["qty"] for item in cart if item["type"] != "physique")
    has_physique = any(item["type"] == "physique" for item in cart)
    has_digital = any(item["type"] != "physique" for item in cart)
    return render_template(
        "panier.html", cart=cart, total=total, physique_total=physique_total,
        digital_total=digital_total, has_physique=has_physique, has_digital=has_digital,
        payment_methods=PAYMENT_METHODS, cart_count=cart_count()
    )


@app.route("/panier/ajouter/<product_id>", methods=["POST"])
def panier_ajouter(product_id):
    db = get_db()
    product = db.execute("SELECT * FROM products WHERE id=?", (product_id,)).fetchone()
    db.close()
    if not product:
        return redirect(url_for("catalogue"))

    cart = get_cart()
    existing = next((i for i in cart if i["id"] == product_id), None)
    if existing:
        existing["qty"] += 1
    else:
        cart.append({
            "id": product["id"], "name": product["name"], "type": product["type"],
            "price": product["price"], "icon": product["icon"], "image": product["image"],
            "digital_content": product["digital_content"], "qty": 1
        })
    save_cart(cart)
    return redirect(request.referrer or url_for("catalogue"))


@app.route("/panier/maj/<product_id>/<action>", methods=["POST"])
def panier_maj(product_id, action):
    cart = get_cart()
    for item in cart:
        if item["id"] == product_id:
            if action == "inc":
                item["qty"] += 1
            elif action == "dec":
                item["qty"] -= 1
    cart = [i for i in cart if i["qty"] > 0]
    if action == "remove":
        cart = [i for i in cart if i["id"] != product_id]
    save_cart(cart)
    return redirect(url_for("panier"))


@app.route("/panier/commander", methods=["POST"])
def panier_commander():
    cart = get_cart()
    if not cart:
        return redirect(url_for("panier"))

    db = get_db()
    cart_ref = gen_id("PANIER")
    payment_method = request.form.get("payment_method", "airtel")
    customer = {
        "customer_name": request.form.get("nom", ""),
        "customer_firstname": request.form.get("prenom", ""),
        "phone": request.form.get("phone", ""),
        "quartier": request.form.get("quartier", ""),
    }
    proof = request.form.get("proof", "")

    for item in cart:
        qty_label = f" (x{item['qty']})" if item["qty"] > 1 else ""
        order = {
            "id": gen_id(),
            "cart_ref": cart_ref,
            "product_id": item["id"],
            "product_name": item["name"] + qty_label,
            "type": item["type"],
            "price": item["price"] * item["qty"],
            **customer,
            "payment_method": "livraison" if item["type"] == "physique" else payment_method,
            "proof": "" if item["type"] == "physique" else proof,
            "digital_content": item.get("digital_content"),
            "status": "a_livrer" if item["type"] == "physique" else "en_attente",
            "created_at": datetime.utcnow().isoformat(),
        }
        db.execute(
            """INSERT INTO orders (id, cart_ref, product_id, product_name, type, price,
               customer_name, customer_firstname, phone, quartier, payment_method, proof,
               digital_content, status, created_at)
               VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            tuple(order.values())
        )
    db.commit()
    db.close()
    save_cart([])
    return render_template("panier.html", cart=[], confirmation=True, cart_count=0)


# ---------- SUIVI DE COMMANDE ----------

@app.route("/suivi", methods=["GET", "POST"])
def suivi():
    orders = None
    if request.method == "POST":
        phone = request.form.get("phone", "").replace(" ", "")
        db = get_db()
        orders = db.execute(
            "SELECT * FROM orders WHERE REPLACE(phone, ' ', '') = ? ORDER BY created_at DESC", (phone,)
        ).fetchall()
        db.close()
    return render_template("suivi.html", orders=orders, cart_count=cart_count())


# ---------- ADMIN ----------

@app.route("/admin", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        if request.form.get("password") == ADMIN_PASSWORD:
            session["admin"] = True
            return redirect(url_for("admin_dashboard"))
        return render_template("admin_login.html", error=True)
    if session.get("admin"):
        return redirect(url_for("admin_dashboard"))
    return render_template("admin_login.html", error=False)


@app.route("/admin/logout")
def admin_logout():
    session.pop("admin", None)
    return redirect(url_for("admin_login"))


def admin_required():
    return session.get("admin", False)


@app.route("/admin/dashboard")
def admin_dashboard():
    if not admin_required():
        return redirect(url_for("admin_login"))
    db = get_db()
    products = db.execute("SELECT * FROM products ORDER BY created_at DESC, id").fetchall()
    orders = db.execute("SELECT * FROM orders ORDER BY created_at DESC").fetchall()
    db.close()
    total_clicks = sum(p["clicks"] for p in products)
    pending = sum(1 for o in orders if o["status"] == "en_attente")
    return render_template(
        "admin.html", products=products, orders=orders, category_labels=CATEGORY_LABELS,
        total_clicks=total_clicks, pending=pending, cart_count=cart_count()
    )


@app.route("/admin/produit/ajouter", methods=["POST"])
def admin_produit_ajouter():
    if not admin_required():
        return redirect(url_for("admin_login"))

    name = request.form.get("name", "").strip()
    price = request.form.get("price", "0")
    if not name or not price:
        return redirect(url_for("admin_dashboard"))

    image_filename = None
    file = request.files.get("image")
    if file and file.filename and allowed_file(file.filename):
        image_filename = secure_filename(gen_id("IMG") + "_" + file.filename)
        os.makedirs(UPLOAD_FOLDER, exist_ok=True)
        file.save(os.path.join(UPLOAD_FOLDER, image_filename))

    db = get_db()
    db.execute(
        """INSERT INTO products (id, name, type, price, description, icon, image, digital_content, clicks, created_at)
           VALUES (?,?,?,?,?,?,?,?,0,?)""",
        (
            gen_id("PROD"), name, request.form.get("type", "physique"), int(price),
            request.form.get("description", ""), request.form.get("icon", "🛍️"),
            ("uploads/" + image_filename) if image_filename else None,
            request.form.get("digital_content", ""), datetime.utcnow().isoformat()
        )
    )
    db.commit()
    db.close()
    return redirect(url_for("admin_dashboard"))


@app.route("/admin/produit/supprimer/<product_id>", methods=["POST"])
def admin_produit_supprimer(product_id):
    if not admin_required():
        return redirect(url_for("admin_login"))
    db = get_db()
    db.execute("DELETE FROM products WHERE id=?", (product_id,))
    db.commit()
    db.close()
    return redirect(url_for("admin_dashboard"))


@app.route("/admin/commande/valider/<order_id>", methods=["POST"])
def admin_commande_valider(order_id):
    if not admin_required():
        return redirect(url_for("admin_login"))
    db = get_db()
    db.execute("UPDATE orders SET status='valide' WHERE id=?", (order_id,))
    db.commit()
    db.close()
    return redirect(url_for("admin_dashboard"))


@app.route("/admin/commande/livrer/<order_id>", methods=["POST"])
def admin_commande_livrer(order_id):
    if not admin_required():
        return redirect(url_for("admin_login"))
    db = get_db()
    db.execute("UPDATE orders SET status='livre' WHERE id=?", (order_id,))
    db.commit()
    db.close()
    return redirect(url_for("admin_dashboard"))


if __name__ == "__main__":
    init_db()
    app.run(debug=True, host="0.0.0.0", port=5000)
