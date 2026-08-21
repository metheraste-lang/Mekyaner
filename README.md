# Mekyaner — Site e-commerce (Flask)

## Lancer le site en local

1. Installer les dépendances :
   pip install -r requirements.txt

2. Démarrer le serveur :
   python app.py

3. Ouvrir dans le navigateur : http://localhost:5000

La base de données SQLite (mekyaner.db) est créée automatiquement au premier lancement, avec des produits de démonstration.

## Avant la mise en ligne — à changer impérativement

Dans app.py :
- `app.secret_key` : remplacer par une vraie clé secrète (aléatoire, longue)
- `ADMIN_PASSWORD` : changer le mot de passe admin (actuellement "mekyaner2026")
- Compléter les numéros MTN Money et Orange Money dans `PAYMENT_METHODS`

## Déploiement

Ce site est une application Python (Flask), pas des fichiers statiques : il faut un hébergement qui supporte Python.

Options simples et abordables :
- Render.com (gratuit pour démarrer)
- Railway.app
- PythonAnywhere

Étapes générales :
1. Mettre le code sur GitHub (ou uploader directement selon l'hébergeur)
2. Créer un nouveau service web Python sur l'hébergeur choisi
3. Commande de démarrage : gunicorn app:app
4. Connecter le nom de domaine une fois acheté

## Structure du projet

- app.py — routes et logique de l'application
- db.py — base de données SQLite (produits, commandes)
- templates/ — pages HTML (Jinja2)
- static/ — style, logo, images uploadées par l'admin
- mekyaner.db — base de données (créée automatiquement)
