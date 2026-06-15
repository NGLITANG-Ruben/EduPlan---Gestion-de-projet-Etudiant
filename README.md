# ProjectFlow — Version Simplifiée (Sans API séparée)

## Structure du projet

```
projectflow-simple/
├── app.py                  ← Point d'entrée unique (tout le backend ici)
├── requirements.txt        ← Dépendances Python
├── basedonnee.db           ← Créée automatiquement au premier lancement
├── static/
│   ├── css/
│   │   ├── main.css        ← Styles globaux + layout
│   │   ├── auth.css        ← Styles page connexion
│   │   └── kanban.css      ← Styles tableau kanban
│   └── js/
│       └── main.js         ← JavaScript global
└── templates/
    ├── base.html           ← Template de base (sidebar, header)
    ├── login.html          ← Page connexion/inscription
    ├── dashboard.html      ← Tableau de bord
    ├── projets.html        ← Liste des projets
    ├── projet_detail.html  ← Détail projet + kanban
    ├── mes_taches.html     ← Mes tâches assignées
    ├── profil.html         ← Mon profil
    └── admin.html          ← Administration (admin uniquement)
```

---

## INSTALLATION ÉTAPE PAR ÉTAPE

### ÉTAPE 1 — Vérifier Python

Ouvrez CMD (Windows) ou Terminal (Mac/Linux).
**Peu importe où vous êtes** pour cette étape :

```
python --version
```

Vous devez voir Python 3.9 ou plus. Si non, téléchargez Python sur python.org.

---

### ÉTAPE 2 — Se placer dans le dossier du projet

Décompressez le ZIP, puis dans le terminal :

**Windows :**
```
cd C:\Users\VotreNom\Downloads\projectflow-simple
```

**Mac/Linux :**
```
cd /home/votreNom/Downloads/projectflow-simple
```

> ⚠️ TOUTES les commandes suivantes se font dans ce dossier.

Vérifiez que vous êtes au bon endroit avec :
```
dir         (Windows)
ls          (Mac/Linux)
```
Vous devez voir app.py, requirements.txt, etc.

---

### ÉTAPE 3 — Créer l'environnement virtuel

Toujours dans le dossier `projectflow-simple/` :

```
python -m venv venv
```

Activez-le :

**Windows :**
```
venv\Scripts\activate
```

**Mac/Linux :**
```
source venv/bin/activate
```

Vous verrez `(venv)` au début de la ligne de commande. C'est bon !

---

### ÉTAPE 4 — Installer les dépendances

Toujours dans `projectflow-simple/`, avec (venv) actif :

```
pip install -r requirements.txt
```

Attendez la fin de l'installation.

---

### ÉTAPE 5 — Lancer l'application

```
python app.py
```

Vous verrez :
```
✓ Base de données initialisée avec données de test
✓ ProjectFlow démarré sur http://localhost:5000
 * Running on http://0.0.0.0:5000
```

---

### ÉTAPE 6 — Ouvrir dans le navigateur

Ouvrez votre navigateur et allez sur :

```
http://localhost:5000
```

Vous arriverez automatiquement sur la page de connexion.

---

## COMPTES DE TEST

| Email | Mot de passe | Rôle |
|-------|-------------|------|
| admin@projectflow.com | password123 | Administrateur |
| alice@projectflow.com | password123 | Membre |
| bob@projectflow.com | password123 | Membre |

---

## ARRÊTER L'APPLICATION

Dans le terminal, appuyez sur `Ctrl + C`.

## RELANCER L'APPLICATION

```
cd projectflow-simple
venv\Scripts\activate    (Windows) ou source venv/bin/activate (Mac/Linux)
python app.py
```

---

## DIFFÉRENCES AVEC LA VERSION API

| Aspect | Version API (Flask+MySQL) | Cette version (Simple) |
|--------|--------------------------|----------------------|
| Base de données | MySQL (serveur externe) | SQLite (fichier local) |
| Communication | Frontend JS → API REST | Formulaires HTML → Flask |
| Fichiers | 28 fichiers séparés | 1 app.py + templates |
| Installation | MySQL requis | Rien d'autre que Python |
| Lancement | 2 terminaux | 1 terminal |
| Fichier DB | basedonnee.db (SQLite) | basedonnee.db (SQLite) |
