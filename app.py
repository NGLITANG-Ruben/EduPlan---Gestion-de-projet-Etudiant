"""
EduPlan - Version etudiante
Flask + SQLite
Multilingue (francais/anglais sans connexion internet)
"""

from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify, g
from flask_bcrypt import Bcrypt
import sqlite3
import os
import json
from datetime import datetime
from functools import wraps

app = Flask(__name__)
app.secret_key = 'eduplan-secret-key-2025'
bcrypt = Bcrypt(app)

DATABASE = 'basedonnee.db'

# ============================================================
# GESTION DES LANGUES (sans connexion internet)
# ============================================================

def load_translation(lang):
    """Charge le fichier JSON de traduction correspondant a la langue"""
    lang_code = lang if lang in ['fr', 'en'] else 'fr'
    try:
        with open(f'translations/{lang_code}.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        with open('translations/fr.json', 'r', encoding='utf-8') as f:
            return json.load(f)

@app.before_request
def before_request():
    """Injecte les traductions dans toutes les requetes"""
    if request.endpoint and request.endpoint.startswith('static'):
        return
    g.lang = session.get('lang', 'fr')
    g.trans = load_translation(g.lang)

@app.context_processor
def inject_trans():
    """Rend les traductions disponibles dans tous les templates"""
    return dict(trans=g.get('trans', {}), lang=g.get('lang', 'fr'))

# ============================================================
# BASE DE DONNEES
# ============================================================

def get_db():
    db = sqlite3.connect(DATABASE)
    db.row_factory = sqlite3.Row
    db.execute("PRAGMA foreign_keys = ON")
    return db

def init_db():
    """Initialise la base de donnees si elle n'existe pas."""
    if os.path.exists(DATABASE):
        return
    db = get_db()
    db.executescript("""
        CREATE TABLE IF NOT EXISTS utilisateurs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT NOT NULL UNIQUE,
            nom TEXT NOT NULL,
            mot_de_passe TEXT NOT NULL,
            role TEXT DEFAULT 'membre',
            date_inscription TEXT DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS projets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            titre TEXT NOT NULL,
            description TEXT DEFAULT '',
            statut TEXT DEFAULT 'actif',
            createur_id INTEGER NOT NULL,
            date_creation TEXT DEFAULT (datetime('now')),
            FOREIGN KEY (createur_id) REFERENCES utilisateurs(id)
        );

        CREATE TABLE IF NOT EXISTS taches (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            projet_id INTEGER NOT NULL,
            titre TEXT NOT NULL,
            description TEXT DEFAULT '',
            statut TEXT DEFAULT 'a_faire',
            priorite TEXT DEFAULT 'normale',
            assigne_a INTEGER,
            echeance TEXT,
            date_creation TEXT DEFAULT (datetime('now')),
            FOREIGN KEY (projet_id) REFERENCES projets(id) ON DELETE CASCADE,
            FOREIGN KEY (assigne_a) REFERENCES utilisateurs(id)
        );

        CREATE TABLE IF NOT EXISTS projet_membres (
            projet_id INTEGER NOT NULL,
            utilisateur_id INTEGER NOT NULL,
            PRIMARY KEY (projet_id, utilisateur_id),
            FOREIGN KEY (projet_id) REFERENCES projets(id) ON DELETE CASCADE,
            FOREIGN KEY (utilisateur_id) REFERENCES utilisateurs(id)
        );

        CREATE TABLE IF NOT EXISTS commentaires (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tache_id INTEGER NOT NULL,
            auteur_id INTEGER NOT NULL,
            contenu TEXT NOT NULL,
            date_creation TEXT DEFAULT (datetime('now')),
            FOREIGN KEY (tache_id) REFERENCES taches(id) ON DELETE CASCADE,
            FOREIGN KEY (auteur_id) REFERENCES utilisateurs(id)
        );
    """)

    # Donnees de test
    admin_hash = bcrypt.generate_password_hash('password123').decode('utf-8')
    db.execute("INSERT INTO utilisateurs (email, nom, mot_de_passe, role) VALUES (?, ?, ?, ?)",
               ('admin@eduplan.com', 'Admin Systeme', admin_hash, 'administrateur'))
    alice_hash = bcrypt.generate_password_hash('password123').decode('utf-8')
    db.execute("INSERT INTO utilisateurs (email, nom, mot_de_passe) VALUES (?, ?, ?)",
               ('alice@eduplan.com', 'Alice Dupont', alice_hash))
    bob_hash = bcrypt.generate_password_hash('password123').decode('utf-8')
    db.execute("INSERT INTO utilisateurs (email, nom, mot_de_passe) VALUES (?, ?, ?)",
               ('bob@eduplan.com', 'Bob Martin', bob_hash))

    db.execute("INSERT INTO projets (titre, description, statut, createur_id) VALUES (?, ?, ?, ?)",
               ('Refonte Site Web', 'Modernisation du site corporate avec nouveau design', 'actif', 1))
    db.execute("INSERT INTO projets (titre, description, statut, createur_id) VALUES (?, ?, ?, ?)",
               ('Application Mobile', 'Developpement app iOS/Android', 'actif', 2))
    db.execute("INSERT INTO projets (titre, description, statut, createur_id) VALUES (?, ?, ?, ?)",
               ('Dashboard Analytics', 'Tableau de bord KPIs en temps reel', 'en_pause', 1))

    db.execute("INSERT INTO projet_membres VALUES (1, 1), (1, 2), (2, 2), (2, 3), (3, 1), (3, 3)")

    db.execute("INSERT INTO taches (projet_id, titre, description, statut, priorite, assigne_a, echeance) VALUES (?, ?, ?, ?, ?, ?, ?)",
               (1, 'Maquettes Figma', 'Creer les maquettes pour toutes les pages', 'termine', 'haute', 2, '2025-12-15'))
    db.execute("INSERT INTO taches (projet_id, titre, description, statut, priorite, assigne_a, echeance) VALUES (?, ?, ?, ?, ?, ?, ?)",
               (1, 'Integration HTML/CSS', 'Integrer les maquettes responsive', 'en_cours', 'haute', 1, '2026-02-01'))
    db.execute("INSERT INTO taches (projet_id, titre, description, statut, priorite, assigne_a, echeance) VALUES (?, ?, ?, ?, ?, ?, ?)",
               (1, 'Tests cross-browser', 'Tester sur tous les navigateurs', 'a_faire', 'normale', 2, '2026-03-01'))
    db.execute("INSERT INTO taches (projet_id, titre, description, statut, priorite, assigne_a, echeance) VALUES (?, ?, ?, ?, ?, ?, ?)",
               (2, 'Architecture backend', 'Definir architecture API REST', 'termine', 'haute', 3, '2025-11-30'))
    db.execute("INSERT INTO taches (projet_id, titre, description, statut, priorite, assigne_a, echeance) VALUES (?, ?, ?, ?, ?, ?, ?)",
               (2, 'Ecran connexion', 'Developper ecran login/inscription', 'en_cours', 'haute', 2, '2026-01-10'))

    db.execute("INSERT INTO commentaires (tache_id, auteur_id, contenu) VALUES (?, ?, ?)",
               (1, 2, 'Les maquettes ont ete validees par le client !'))
    db.execute("INSERT INTO commentaires (tache_id, auteur_id, contenu) VALUES (?, ?, ?)",
               (2, 1, 'Avancement : 60%. Menu mobile en cours.'))

    db.commit()
    db.close()
    print("Base de donnees initialisee avec donnees de test")

# ============================================================
# DECORATEURS D'AUTHENTIFICATION
# ============================================================

def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated

def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        if session.get('user_role') != 'administrateur':
            return redirect(url_for('dashboard'))
        return f(*args, **kwargs)
    return decorated

# ============================================================
# ROUTES PRINCIPALES (avec choix langue)
# ============================================================

@app.route('/')
def index():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return render_template('welcome.html')

@app.route('/set-language/<lang>')
def set_language(lang):
    if lang in ['fr', 'en']:
        session['lang'] = lang
    next_page = request.referrer or url_for('index')
    return redirect(next_page)

@app.route('/skip')
def skip_welcome():
    return redirect(url_for('login'))

# ============================================================
# ROUTES AUTHENTIFICATION
# ============================================================

@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('mot_de_passe', '')
        db = get_db()
        user = db.execute("SELECT * FROM utilisateurs WHERE email = ?", (email,)).fetchone()
        db.close()
        if user and bcrypt.check_password_hash(user['mot_de_passe'], password):
            session['user_id'] = user['id']
            session['user_nom'] = user['nom']
            session['user_role'] = user['role']
            return redirect(url_for('dashboard'))
    return render_template('login.html', show_register=False)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        nom = request.form.get('nom', '').strip()
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('mot_de_passe', '')
        if not nom or not email or not password:
            return render_template('login.html', show_register=True)
        if len(password) < 6:
            return render_template('login.html', show_register=True)
        db = get_db()
        existing = db.execute("SELECT id FROM utilisateurs WHERE email = ?", (email,)).fetchone()
        if existing:
            db.close()
            return render_template('login.html', show_register=True)
        hashed = bcrypt.generate_password_hash(password).decode('utf-8')
        cur = db.execute("INSERT INTO utilisateurs (email, nom, mot_de_passe) VALUES (?, ?, ?)",
                         (email, nom, hashed))
        db.commit()
        user_id = cur.lastrowid
        db.close()
        session['user_id'] = user_id
        session['user_nom'] = nom
        session['user_role'] = 'membre'
        return redirect(url_for('dashboard'))
    return render_template('login.html', show_register=True)

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

# ============================================================
# DASHBOARD
# ============================================================

@app.route('/dashboard')
@login_required
def dashboard():
    db = get_db()
    uid = session['user_id']

    projets = db.execute("""
        SELECT DISTINCT p.*, u.nom as createur_nom,
               (SELECT COUNT(*) FROM taches t WHERE t.projet_id = p.id) as nb_taches,
               (SELECT COUNT(*) FROM taches t WHERE t.projet_id = p.id AND t.statut = 'termine') as nb_terminees
        FROM projets p
        LEFT JOIN projet_membres pm ON pm.projet_id = p.id
        JOIN utilisateurs u ON u.id = p.createur_id
        WHERE pm.utilisateur_id = ? OR p.createur_id = ?
        ORDER BY p.date_creation DESC LIMIT 5
    """, (uid, uid)).fetchall()

    stats = {
        'projets_actifs': db.execute("""
            SELECT COUNT(DISTINCT p.id) FROM projets p
            LEFT JOIN projet_membres pm ON pm.projet_id = p.id
            WHERE (pm.utilisateur_id = ? OR p.createur_id = ?) AND p.statut = 'actif'
        """, (uid, uid)).fetchone()[0],
        'taches_en_cours': db.execute("""
            SELECT COUNT(t.id) FROM taches t
            JOIN projets p ON p.id = t.projet_id
            LEFT JOIN projet_membres pm ON pm.projet_id = p.id
            WHERE (pm.utilisateur_id = ? OR p.createur_id = ?) AND t.statut = 'en_cours'
        """, (uid, uid)).fetchone()[0],
        'taches_terminees': db.execute("""
            SELECT COUNT(t.id) FROM taches t
            JOIN projets p ON p.id = t.projet_id
            LEFT JOIN projet_membres pm ON pm.projet_id = p.id
            WHERE (pm.utilisateur_id = ? OR p.createur_id = ?) AND t.statut = 'termine'
        """, (uid, uid)).fetchone()[0],
        'mes_taches': db.execute(
            "SELECT COUNT(*) FROM taches WHERE assigne_a = ? AND statut != 'termine'", (uid,)
        ).fetchone()[0],
    }

    mes_taches = db.execute("""
        SELECT t.*, p.titre as projet_titre
        FROM taches t JOIN projets p ON p.id = t.projet_id
        WHERE t.assigne_a = ? AND t.statut != 'termine'
        ORDER BY t.echeance ASC LIMIT 6
    """, (uid,)).fetchall()

    db.close()
    return render_template('dashboard.html', projets=projets, stats=stats, mes_taches=mes_taches)

# ============================================================
# PROJETS
# ============================================================

@app.route('/projets')
@login_required
def projets():
    db = get_db()
    uid = session['user_id']
    search = request.args.get('search', '').strip()
    statut = request.args.get('statut', '')
    page = int(request.args.get('page', 1))
    per_page = 9
    offset = (page - 1) * per_page

    where = "WHERE (pm.utilisateur_id = ? OR p.createur_id = ?)"
    params = [uid, uid]

    if search:
        where += " AND (p.titre LIKE ? OR p.description LIKE ?)"
        params += [f'%{search}%', f'%{search}%']
    if statut:
        where += " AND p.statut = ?"
        params.append(statut)

    total = db.execute(f"""
        SELECT COUNT(DISTINCT p.id) FROM projets p
        LEFT JOIN projet_membres pm ON pm.projet_id = p.id {where}
    """, params).fetchone()[0]

    projets_list = db.execute(f"""
        SELECT DISTINCT p.*, u.nom as createur_nom,
               (SELECT COUNT(*) FROM taches t WHERE t.projet_id = p.id) as nb_taches,
               (SELECT COUNT(*) FROM taches t WHERE t.projet_id = p.id AND t.statut = 'termine') as nb_terminees
        FROM projets p
        LEFT JOIN projet_membres pm ON pm.projet_id = p.id
        JOIN utilisateurs u ON u.id = p.createur_id
        {where}
        ORDER BY p.date_creation DESC
        LIMIT ? OFFSET ?
    """, params + [per_page, offset]).fetchall()

    db.close()
    pages = (total + per_page - 1) // per_page
    return render_template('projets.html', projets=projets_list, total=total,
                           page=page, pages=pages, search=search, statut_filtre=statut)

@app.route('/projets/creer', methods=['POST'])
@login_required
def creer_projet():
    titre = request.form.get('titre', '').strip()
    description = request.form.get('description', '').strip()
    if not titre:
        return redirect(url_for('projets'))
    db = get_db()
    uid = session['user_id']
    cur = db.execute("INSERT INTO projets (titre, description, createur_id) VALUES (?, ?, ?)",
                     (titre, description, uid))
    projet_id = cur.lastrowid
    db.execute("INSERT INTO projet_membres VALUES (?, ?)", (projet_id, uid))
    db.commit()
    db.close()
    return redirect(url_for('projet_detail', projet_id=projet_id))

@app.route('/projets/<int:projet_id>')
@login_required
def projet_detail(projet_id):
    db = get_db()
    uid = session['user_id']

    projet = db.execute("""
        SELECT p.*, u.nom as createur_nom FROM projets p
        JOIN utilisateurs u ON u.id = p.createur_id WHERE p.id = ?
    """, (projet_id,)).fetchone()

    if not projet:
        return redirect(url_for('projets'))

    membres = db.execute("""
        SELECT u.id, u.nom, u.email FROM projet_membres pm
        JOIN utilisateurs u ON u.id = pm.utilisateur_id WHERE pm.projet_id = ?
    """, (projet_id,)).fetchall()

    filtre_statut = request.args.get('statut', '')
    filtre_priorite = request.args.get('priorite', '')

    q = "SELECT t.*, u.nom as assigne_nom FROM taches t LEFT JOIN utilisateurs u ON u.id = t.assigne_a WHERE t.projet_id = ?"
    params = [projet_id]
    if filtre_statut:
        q += " AND t.statut = ?"
        params.append(filtre_statut)
    if filtre_priorite:
        q += " AND t.priorite = ?"
        params.append(filtre_priorite)
    q += " ORDER BY CASE t.priorite WHEN 'haute' THEN 1 WHEN 'normale' THEN 2 ELSE 3 END, t.echeance ASC"
    taches = db.execute(q, params).fetchall()

    taches_kanban = {'a_faire': [], 'en_cours': [], 'termine': []}
    for t in taches:
        taches_kanban[t['statut']].append(t)

    db.close()
    return render_template('projet_detail.html', projet=projet, membres=membres,
                           taches=taches, taches_kanban=taches_kanban,
                           filtre_statut=filtre_statut, filtre_priorite=filtre_priorite,
                           uid=uid)

@app.route('/projets/<int:projet_id>/modifier', methods=['POST'])
@login_required
def modifier_projet(projet_id):
    db = get_db()
    projet = db.execute("SELECT * FROM projets WHERE id = ?", (projet_id,)).fetchone()
    if not projet or str(projet['createur_id']) != str(session['user_id']):
        db.close()
        return redirect(url_for('projets'))
    titre = request.form.get('titre', '').strip()
    description = request.form.get('description', '').strip()
    statut = request.form.get('statut', 'actif')
    db.execute("UPDATE projets SET titre=?, description=?, statut=? WHERE id=?",
               (titre, description, statut, projet_id))
    db.commit()
    db.close()
    return redirect(url_for('projet_detail', projet_id=projet_id))

@app.route('/projets/<int:projet_id>/supprimer', methods=['POST'])
@login_required
def supprimer_projet(projet_id):
    db = get_db()
    projet = db.execute("SELECT * FROM projets WHERE id = ?", (projet_id,)).fetchone()
    user_role = session.get('user_role')
    if not projet or (str(projet['createur_id']) != str(session['user_id']) and user_role != 'administrateur'):
        db.close()
        return redirect(url_for('projets'))
    db.execute("DELETE FROM projets WHERE id = ?", (projet_id,))
    db.commit()
    db.close()
    return redirect(url_for('projets'))

@app.route('/projets/<int:projet_id>/ajouter-membre', methods=['POST'])
@login_required
def ajouter_membre(projet_id):
    email = request.form.get('email', '').strip().lower()
    db = get_db()
    user = db.execute("SELECT id, nom FROM utilisateurs WHERE email = ?", (email,)).fetchone()
    if user:
        existing = db.execute("SELECT 1 FROM projet_membres WHERE projet_id=? AND utilisateur_id=?",
                              (projet_id, user['id'])).fetchone()
        if not existing:
            db.execute("INSERT INTO projet_membres VALUES (?, ?)", (projet_id, user['id']))
            db.commit()
    db.close()
    return redirect(url_for('projet_detail', projet_id=projet_id))

# ============================================================
# TACHES
# ============================================================

@app.route('/projets/<int:projet_id>/taches/creer', methods=['POST'])
@login_required
def creer_tache(projet_id):
    titre = request.form.get('titre', '').strip()
    if not titre:
        return redirect(url_for('projet_detail', projet_id=projet_id))
    description = request.form.get('description', '').strip()
    statut = request.form.get('statut', 'a_faire')
    priorite = request.form.get('priorite', 'normale')
    assigne_a = request.form.get('assigne_a') or None
    echeance = request.form.get('echeance') or None
    db = get_db()
    db.execute("INSERT INTO taches (projet_id, titre, description, statut, priorite, assigne_a, echeance) VALUES (?,?,?,?,?,?,?)",
               (projet_id, titre, description, statut, priorite, assigne_a, echeance))
    db.commit()
    db.close()
    return redirect(url_for('projet_detail', projet_id=projet_id))

@app.route('/taches/<int:tache_id>/modifier', methods=['POST'])
@login_required
def modifier_tache(tache_id):
    db = get_db()
    tache = db.execute("SELECT * FROM taches WHERE id = ?", (tache_id,)).fetchone()
    if not tache:
        db.close()
        return redirect(url_for('projets'))
    titre = request.form.get('titre', tache['titre']).strip()
    description = request.form.get('description', tache['description'])
    statut = request.form.get('statut', tache['statut'])
    priorite = request.form.get('priorite', tache['priorite'])
    assigne_a = request.form.get('assigne_a') or None
    echeance = request.form.get('echeance') or None
    db.execute("UPDATE taches SET titre=?, description=?, statut=?, priorite=?, assigne_a=?, echeance=? WHERE id=?",
               (titre, description, statut, priorite, assigne_a, echeance, tache_id))
    db.commit()
    projet_id = tache['projet_id']
    db.close()
    return redirect(url_for('projet_detail', projet_id=projet_id))

@app.route('/taches/<int:tache_id>/statut', methods=['POST'])
@login_required
def changer_statut(tache_id):
    """Route AJAX pour le drag & drop kanban."""
    data = request.get_json()
    nouveau_statut = data.get('statut')
    if nouveau_statut not in ['a_faire', 'en_cours', 'termine']:
        return jsonify({'error': 'Statut invalide'}), 400
    db = get_db()
    db.execute("UPDATE taches SET statut = ? WHERE id = ?", (nouveau_statut, tache_id))
    db.commit()
    db.close()
    return jsonify({'success': True})

@app.route('/taches/<int:tache_id>/supprimer', methods=['POST'])
@login_required
def supprimer_tache(tache_id):
    db = get_db()
    tache = db.execute("SELECT projet_id FROM taches WHERE id = ?", (tache_id,)).fetchone()
    if tache:
        projet_id = tache['projet_id']
        db.execute("DELETE FROM taches WHERE id = ?", (tache_id,))
        db.commit()
        db.close()
        return redirect(url_for('projet_detail', projet_id=projet_id))
    db.close()
    return redirect(url_for('projets'))

@app.route('/taches/<int:tache_id>/commentaire', methods=['POST'])
@login_required
def ajouter_commentaire(tache_id):
    contenu = request.form.get('contenu', '').strip()
    if contenu:
        db = get_db()
        db.execute("INSERT INTO commentaires (tache_id, auteur_id, contenu) VALUES (?,?,?)",
                   (tache_id, session['user_id'], contenu))
        db.commit()
        db.close()
    return redirect(request.referrer or url_for('projets'))

@app.route('/taches/<int:tache_id>/commentaires')
@login_required
def get_commentaires(tache_id):
    db = get_db()
    comments = db.execute("""
        SELECT c.*, u.nom as auteur_nom FROM commentaires c
        JOIN utilisateurs u ON u.id = c.auteur_id
        WHERE c.tache_id = ? ORDER BY c.date_creation ASC
    """, (tache_id,)).fetchall()
    db.close()
    return jsonify([dict(c) for c in comments])

# ============================================================
# MES TACHES
# ============================================================

@app.route('/mes-taches')
@login_required
def mes_taches():
    db = get_db()
    uid = session['user_id']
    filtre_statut = request.args.get('statut', '')
    filtre_priorite = request.args.get('priorite', '')

    q = """
        SELECT t.*, p.titre as projet_titre, p.id as projet_id
        FROM taches t JOIN projets p ON p.id = t.projet_id
        WHERE t.assigne_a = ?
    """
    params = [uid]
    if filtre_statut:
        q += " AND t.statut = ?"
        params.append(filtre_statut)
    if filtre_priorite:
        q += " AND t.priorite = ?"
        params.append(filtre_priorite)
    q += " ORDER BY CASE t.statut WHEN 'en_cours' THEN 1 WHEN 'a_faire' THEN 2 ELSE 3 END, t.echeance ASC"
    taches = db.execute(q, params).fetchall()
    db.close()
    return render_template('mes_taches.html', taches=taches,
                           filtre_statut=filtre_statut, filtre_priorite=filtre_priorite)

# ============================================================
# PROFIL
# ============================================================

@app.route('/profil', methods=['GET', 'POST'])
@login_required
def profil():
    db = get_db()
    uid = session['user_id']
    if request.method == 'POST':
        nom = request.form.get('nom', '').strip()
        if nom:
            db.execute("UPDATE utilisateurs SET nom = ? WHERE id = ?", (nom, uid))
            db.commit()
            session['user_nom'] = nom
    user = db.execute("SELECT * FROM utilisateurs WHERE id = ?", (uid,)).fetchone()
    db.close()
    return render_template('profil.html', user=user)

# ============================================================
# ADMINISTRATION
# ============================================================

@app.route('/admin')
@admin_required
def admin():
    db = get_db()
    search = request.args.get('search', '').strip()
    if search:
        users = db.execute("SELECT * FROM utilisateurs WHERE nom LIKE ? OR email LIKE ? ORDER BY nom",
                           (f'%{search}%', f'%{search}%')).fetchall()
    else:
        users = db.execute("SELECT * FROM utilisateurs ORDER BY nom").fetchall()
    db.close()
    return render_template('admin.html', users=users, search=search)

@app.route('/admin/role/<int:user_id>', methods=['POST'])
@admin_required
def changer_role(user_id):
    if user_id == session['user_id']:
        return redirect(url_for('admin'))
    db = get_db()
    user = db.execute("SELECT role FROM utilisateurs WHERE id = ?", (user_id,)).fetchone()
    if user:
        new_role = 'membre' if user['role'] == 'administrateur' else 'administrateur'
        db.execute("UPDATE utilisateurs SET role = ? WHERE id = ?", (new_role, user_id))
        db.commit()
    db.close()
    return redirect(url_for('admin'))

# ============================================================
# LANCEMENT
# ============================================================

if __name__ == '__main__':
    init_db()
    print("EduPlan demarre sur http://localhost:5000")
    app.run(debug=True, host='0.0.0.0', port=5000)