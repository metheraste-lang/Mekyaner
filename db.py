import os
import psycopg2
import psycopg2.extras


def get_db():
    conn = psycopg2.connect(os.environ["DATABASE_URL"], cursor_factory=psycopg2.extras.RealDictCursor)
    return conn


def init_db():
    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS products (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            type TEXT NOT NULL,
            price INTEGER NOT NULL,
            description TEXT,
            icon TEXT,
            image TEXT,
            digital_content TEXT,
            clicks INTEGER DEFAULT 0,
            created_at TEXT
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS orders (
            id TEXT PRIMARY KEY,
            cart_ref TEXT,
            product_id TEXT,
            product_name TEXT,
            type TEXT,
            price INTEGER,
            customer_name TEXT,
            customer_firstname TEXT,
            phone TEXT,
            quartier TEXT,
            payment_method TEXT,
            proof TEXT,
            digital_content TEXT,
            status TEXT,
            created_at TEXT
        )
    """)
    conn.commit()

    cur.execute("SELECT COUNT(*) AS c FROM products")
    count = cur.fetchone()["c"]
    if count == 0:
        seed = [
            ("p1", "Accessoire auto premium", "physique", 129900, "Accessoire pratique et durable pour votre véhicule.", "🚗", None, None),
            ("p2", "Coque smartphone renforcée", "physique", 8500, "Protection robuste pour smartphone, plusieurs coloris.", "📱", None, None),
            ("p3", "Objet déco maison", "physique", 42000, "Pièce déco pour sublimer votre intérieur.", "🏠", None, None),
            ("p4", "Sneakers édition limitée", "physique", 35000, "Paire exclusive, plusieurs pointures disponibles.", "👟", None, None),
            ("p5", "Kit d'accessoires électroniques", "physique", 18500, "Câbles, adaptateurs et supports essentiels.", "🔌", None, None),
            ("p6", "Terrain viabilisé — dossier", "physique", 2500000, "Dossier complet pour terrain viabilisé, zone en développement.", "🏘️", None, None),
            ("p7", "Pack templates business", "digital", 8000, "Modèles prêts à l'emploi pour vos documents pro.", "🗂️", None, "https://exemple.com/telechargement/pack-templates"),
            ("p8", "Pack de designs graphiques", "digital", 6500, "Visuels et gabarits prêts à personnaliser.", "🎨", None, "https://exemple.com/telechargement/designs"),
            ("p9", "Modèle de budget personnel", "digital", 4000, "Feuille de calcul pour suivre ses revenus et dépenses.", "📊", None, "https://exemple.com/telechargement/budget"),
            ("p10", "Investir dans l'immobilier", "formation", 35000, "Formation complète pour démarrer dans l'immobilier.", "🎓", None, "https://exemple.com/formation/immobilier"),
            ("p11", "Créer son entreprise en ligne", "formation", 25000, "De l'idée au lancement, étape par étape.", "💼", None, "https://exemple.com/formation/entreprise"),
            ("p12", "Marketing digital — les bases", "formation", 20000, "Les fondamentaux pour promouvoir une activité en ligne.", "📈", None, "https://exemple.com/formation/marketing"),
        ]
        cur.executemany(
            "INSERT INTO products (id, name, type, price, description, icon, image, digital_content) VALUES (%s,%s,%s,%s,%s,%s,%s,%s)",
            seed
        )
        conn.commit()
    conn.close()
