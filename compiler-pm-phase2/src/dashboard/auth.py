"""
Auth Module — Neo-Sousse Smart City
Google OAuth 2.0 Sign-In Only — Clean & Professional
"""

import hashlib
import secrets
import logging
from urllib.parse import urlencode
from datetime import datetime
from typing import Optional, Dict, Tuple

logger = logging.getLogger(__name__)

try:
    import requests as req_lib
except ImportError:
    req_lib = None

try:
    import mysql.connector as _mysql_auth
except ImportError:
    _mysql_auth = None

# ═══════════════════════════════════════════════════════════════════
# CONFIG
# ═══════════════════════════════════════════════════════════════════
import os
ADMIN_EMAIL = "firasmrabet1603@gmail.com"

GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID", "")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET", "")
GOOGLE_REDIRECT_URI = "http://localhost:8502"
GOOGLE_AUTH_ENDPOINT = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_ENDPOINT = "https://oauth2.googleapis.com/token"
GOOGLE_USERINFO_ENDPOINT = "https://www.googleapis.com/oauth2/v3/userinfo"

GOOGLE_G_SVG = '<svg width="22" height="22" viewBox="0 0 48 48"><path fill="#EA4335" d="M24 9.5c3.54 0 6.71 1.22 9.21 3.6l6.85-6.85C35.9 2.38 30.47 0 24 0 14.62 0 6.51 5.38 2.56 13.22l7.98 6.19C12.43 13.72 17.74 9.5 24 9.5z"/><path fill="#4285F4" d="M46.98 24.55c0-1.57-.15-3.09-.38-4.55H24v9.02h12.94c-.58 2.96-2.26 5.48-4.78 7.18l7.73 6c4.51-4.18 7.09-10.36 7.09-17.65z"/><path fill="#FBBC05" d="M10.53 28.59c-.48-1.45-.76-2.99-.76-4.59s.27-3.14.76-4.59l-7.98-6.19C.92 16.46 0 20.12 0 24c0 3.88.92 7.54 2.56 10.78l7.97-6.19z"/><path fill="#34A853" d="M24 48c6.48 0 11.93-2.13 15.89-5.81l-7.73-6c-2.15 1.45-4.92 2.3-8.16 2.3-6.26 0-11.57-4.22-13.47-9.91l-7.98 6.19C6.51 42.62 14.62 48 24 48z"/></svg>'


# ═══════════════════════════════════════════════════════════════════
# GOOGLE OAUTH
# ═══════════════════════════════════════════════════════════════════
def get_google_auth_url() -> str:
    params = {
        "client_id": GOOGLE_CLIENT_ID,
        "redirect_uri": GOOGLE_REDIRECT_URI,
        "response_type": "code",
        "scope": "openid email profile",
        "access_type": "offline",
        "prompt": "select_account",
    }
    return f"{GOOGLE_AUTH_ENDPOINT}?{urlencode(params)}"


def exchange_google_code(code: str) -> Tuple[bool, str, Optional[Dict]]:
    if not req_lib:
        return False, "Module 'requests' non installé", None
    try:
        token_resp = req_lib.post(GOOGLE_TOKEN_ENDPOINT, data={
            "code": code,
            "client_id": GOOGLE_CLIENT_ID,
            "client_secret": GOOGLE_CLIENT_SECRET,
            "redirect_uri": GOOGLE_REDIRECT_URI,
            "grant_type": "authorization_code",
        }, timeout=10)
        if token_resp.status_code != 200:
            return False, f"Erreur Google OAuth: {token_resp.text}", None
        tokens = token_resp.json()
        access_token = tokens.get("access_token")
        if not access_token:
            return False, "Token d'accès non reçu", None
        info_resp = req_lib.get(
            GOOGLE_USERINFO_ENDPOINT,
            headers={"Authorization": f"Bearer {access_token}"},
            timeout=10
        )
        if info_resp.status_code != 200:
            return False, f"Erreur info utilisateur: {info_resp.text}", None
        user_info = info_resp.json()
        return True, "OK", {
            "email": user_info.get("email", ""),
            "name": user_info.get("name", ""),
            "sub": user_info.get("sub", ""),
            "picture": user_info.get("picture", ""),
        }
    except Exception as e:
        return False, f"Erreur OAuth: {e}", None


# ═══════════════════════════════════════════════════════════════════
# ROLES
# ═══════════════════════════════════════════════════════════════════
def detect_role(email: str) -> str:
    email_lower = email.lower().strip()
    if email_lower == ADMIN_EMAIL:
        return "admin"
    local_part = email_lower.split("@")[0] if "@" in email_lower else ""
    if "tech" in local_part and email_lower.endswith("@gmail.com"):
        return "technicien"
    return "citoyen"

def get_pages_for_role(role: str) -> list:
    all_pages = [
        "🏠 Dashboard", "🔤 Compilateur NL→SQL", "🤖 Automates",
        "🚨 Alertes Automatiques", "📊 Capteurs", "🔧 Interventions",
        "👷 Assignation Techniciens", "🚗 Véhicules & Trajets",
        "👥 Citoyens", "📄 Rapports IA",
    ]
    if role == "admin":
        return all_pages
    elif role == "technicien":
        return ["🚨 Alertes Automatiques", "🔧 Interventions"]
    else:
        return ["👥 Citoyens", "🚗 Véhicules & Trajets", "📊 Capteurs"]


# ═══════════════════════════════════════════════════════════════════
# DATABASE — Dedicated connection (not shared singleton)
# ═══════════════════════════════════════════════════════════════════
def _auth_conn():
    if not _mysql_auth:
        return None
    try:
        return _mysql_auth.connect(
            host="127.0.0.1", port=3306, user="root", password="",
            database="sousse_smart_city_projet_module",
            charset='utf8mb4', use_pure=True, autocommit=True, connection_timeout=5
        )
    except Exception as e:
        logger.error(f"Auth DB error: {e}")
        return None

def _auth_execute(query, params=None):
    conn = _auth_conn()
    if not conn: return False
    try:
        cur = conn.cursor()
        cur.execute(query, params or ())
        conn.commit()
        return True
    except Exception as e:
        logger.error(f"Auth exec error: {e}")
        return False
    finally:
        try: conn.close()
        except: pass

def _auth_fetch_one(query, params=None):
    conn = _auth_conn()
    if not conn: return None
    try:
        cur = conn.cursor(dictionary=True, buffered=True)
        cur.execute(query, params or ())
        return cur.fetchone()
    except Exception as e:
        logger.error(f"Auth fetch error: {e}")
        return None
    finally:
        try: conn.close()
        except: pass

def init_auth_tables():
    _auth_execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INT AUTO_INCREMENT PRIMARY KEY,
            email VARCHAR(255) UNIQUE NOT NULL,
            password_hash VARCHAR(255) DEFAULT '',
            nom VARCHAR(100) DEFAULT '',
            role ENUM('admin','citoyen','technicien') NOT NULL DEFAULT 'citoyen',
            google_id VARCHAR(100) DEFAULT NULL,
            avatar_url VARCHAR(500) DEFAULT NULL,
            reset_code VARCHAR(6) DEFAULT NULL,
            reset_code_expiry DATETIME DEFAULT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            last_login DATETIME DEFAULT NULL,
            is_active BOOLEAN DEFAULT TRUE
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
    """)

def register_google_user(email, nom, google_id, avatar_url=""):
    email = email.strip().lower()
    try:
        ex = _auth_fetch_one("SELECT id,email,nom,role,is_active FROM users WHERE email=%s", (email,))
        if ex:
            if not ex.get('is_active', True):
                return False, "Compte désactivé", None
            _auth_execute(
                "UPDATE users SET last_login=NOW(),google_id=%s,avatar_url=%s WHERE id=%s",
                (google_id, avatar_url, ex['id'])
            )
            return True, "Connexion réussie", {
                "id": ex['id'], "email": ex['email'], "nom": ex.get('nom', ''),
                "role": ex['role'], "avatar": avatar_url
            }
        else:
            role = detect_role(email)
            _auth_execute(
                "INSERT INTO users (email,password_hash,nom,role,google_id,avatar_url,last_login) "
                "VALUES(%s,%s,%s,%s,%s,%s,NOW())",
                (email, secrets.token_hex(16), nom, role, google_id, avatar_url)
            )
            nu = _auth_fetch_one("SELECT id FROM users WHERE email=%s", (email,))
            rn = {"admin": "Administrateur", "technicien": "Technicien", "citoyen": "Citoyen"}
            return True, f"Bienvenue! Rôle: {rn.get(role, role)}", {
                "id": nu['id'] if nu else 0, "email": email, "nom": nom,
                "role": role, "avatar": avatar_url
            }
    except Exception as e:
        return False, f"Erreur: {e}", None


# ═══════════════════════════════════════════════════════════════════
# PREMIUM LOGIN PAGE — Google Only
# ═══════════════════════════════════════════════════════════════════

def render_login_page(st):
    """Render premium Google-only sign-in page."""

    if "auth_user" not in st.session_state:
        st.session_state.auth_user = None
    if "google_oauth_error" not in st.session_state:
        st.session_state.google_oauth_error = None

    if st.session_state.auth_user:
        return True

    init_auth_tables()

    # ── Handle Google OAuth callback ──
    try:
        query_params = st.query_params
        google_code = query_params.get("code")
    except AttributeError:
        query_params = st.experimental_get_query_params()
        google_code = query_params.get("code", [None])[0]

    if google_code:
        with st.spinner("Connexion en cours..."):
            ok, msg, ginfo = exchange_google_code(google_code)
        try:
            st.query_params.clear()
        except AttributeError:
            st.experimental_set_query_params()

        if ok and ginfo:
            email = ginfo.get("email", "")
            name = ginfo.get("name", "")
            sub = ginfo.get("sub", "")
            avatar = ginfo.get("picture", "")
            reg_ok, reg_msg, user_data = register_google_user(email, name, sub, avatar)
            if reg_ok and user_data:
                st.session_state.auth_user = user_data
                st.rerun()
            else:
                st.session_state.google_oauth_error = reg_msg
        else:
            st.session_state.google_oauth_error = msg

    # ═══════════════════════════════════════════
    # HIDE STREAMLIT CHROME
    # ═══════════════════════════════════════════
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap');
    [data-testid="stHeader"] { background: transparent !important; }
    [data-testid="stSidebar"] { display: none !important; }
    [data-testid="stToolbar"] { display: none !important; }
    footer, #MainMenu { display: none !important; }
    [data-testid="stAppViewContainer"] {
        background: linear-gradient(135deg, #020617 0%, #0f172a 35%, #1e1b4b 65%, #020617 100%) !important;
    }
    iframe { border: none !important; }
    </style>
    """, unsafe_allow_html=True)

    # ═══════════════════════════════════════════
    # RENDER CARD — Split: iframe for design, native button for Google
    # ═══════════════════════════════════════════
    import streamlit.components.v1 as _login_comp

    auth_url = get_google_auth_url()

    # ── Part 1: Top card (brand + welcome) ──
    top_html = f"""
    <!DOCTYPE html><html><head><meta charset="utf-8">
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap" rel="stylesheet">
    <style>
    * {{ margin:0; padding:0; box-sizing:border-box; }}
    body {{ background:transparent; font-family:'Inter',sans-serif; }}
    .card {{
        max-width:440px; margin:0 auto;
        background:rgba(15,23,42,0.92);
        backdrop-filter:blur(40px) saturate(1.8);
        border:1px solid rgba(59,130,246,0.15);
        border-radius:28px 28px 0 0;
        border-bottom:none;
        padding:3rem 2.5rem 1.5rem;
        box-shadow:0 -10px 60px rgba(0,0,0,0.3);
        position:relative; overflow:hidden;
    }}
    .card::before {{
        content:''; position:absolute; top:0;left:0;right:0; height:3px;
        background:linear-gradient(90deg,#3b82f6,#8b5cf6,#06b6d4,#22c55e);
        border-radius:28px 28px 0 0;
    }}
    .brand {{ text-align:center; margin-bottom:1.8rem; }}
    .brand-icon {{
        display:inline-flex; align-items:center; justify-content:center;
        width:72px; height:72px; border-radius:20px;
        background:linear-gradient(135deg,rgba(59,130,246,0.18),rgba(139,92,246,0.18));
        border:1px solid rgba(59,130,246,0.25);
        margin-bottom:1rem;
        box-shadow:0 12px 30px rgba(59,130,246,0.12);
        animation:pulse 3s ease-in-out infinite;
    }}
    @keyframes pulse {{
        0%,100%{{ box-shadow:0 12px 30px rgba(59,130,246,0.12); }}
        50%{{ box-shadow:0 12px 40px rgba(59,130,246,0.25); }}
    }}
    .brand-icon span {{ font-size:2.2rem; }}
    .brand-title {{
        font-size:1.6rem; font-weight:800;
        background:linear-gradient(135deg,#f1f5f9,#94a3b8);
        -webkit-background-clip:text; -webkit-text-fill-color:transparent;
        margin-bottom:0.3rem;
    }}
    .brand-sub {{ font-size:0.72rem; color:#475569; letter-spacing:2.5px; text-transform:uppercase; font-weight:500; }}
    .welcome {{ text-align:center; }}
    .welcome h3 {{ font-size:1.15rem; font-weight:600; color:#e2e8f0; margin-bottom:0.5rem; }}
    .welcome p {{ font-size:0.82rem; color:#64748b; line-height:1.6; }}
    </style>
    </head><body>
    <div class="card">
        <div class="brand">
            <div class="brand-icon"><span>🏙️</span></div>
            <div class="brand-title">Neo-Sousse Smart City</div>
            <div class="brand-sub">Plateforme IoT · Phase 2</div>
        </div>
        <div class="welcome">
            <h3>Bienvenue</h3>
            <p>Connectez-vous avec votre compte Google<br>pour accéder à la plateforme de monitoring.</p>
        </div>
    </div>
    </body></html>
    """
    _login_comp.html(top_html, height=330, scrolling=False)

    # ── Part 2: Native Google Sign-In Button (styled to match card) ──
    st.markdown(f"""
    <style>
    /* Seamless card-style wrapper for the Google button */
    .google-btn-wrap {{
        max-width: 440px; margin: -2.5rem auto 0;
        padding: 0 2.5rem;
        background: rgba(15,23,42,0.92);
        border-left: 1px solid rgba(59,130,246,0.15);
        border-right: 1px solid rgba(59,130,246,0.15);
    }}
    .google-btn-wrap a {{
        display: flex; align-items: center; justify-content: center; gap: 12px;
        width: 100%; padding: 1rem 1.5rem;
        background: rgba(255,255,255,0.07);
        border: 1px solid rgba(255,255,255,0.12);
        border-radius: 14px; color: #e2e8f0;
        font-family: 'Inter', sans-serif; font-size: 0.95rem; font-weight: 600;
        cursor: pointer; text-decoration: none;
        transition: all 0.3s cubic-bezier(0.4,0,0.2,1);
    }}
    .google-btn-wrap a:hover {{
        background: rgba(255,255,255,0.12);
        border-color: rgba(66,133,244,0.5);
        box-shadow: 0 8px 30px rgba(66,133,244,0.2);
        transform: translateY(-2px); color: #fff;
    }}
    .google-btn-wrap a:active {{ transform: translateY(0); }}
    </style>
    <div class="google-btn-wrap">
        <a href="{auth_url}" target="_self">
            {GOOGLE_G_SVG}
            <span>Continuer avec Google</span>
        </a>
    </div>
    """, unsafe_allow_html=True)

    # ── Part 3: Bottom card (security + features + footer) ──
    bottom_html = f"""
    <!DOCTYPE html><html><head><meta charset="utf-8">
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap" rel="stylesheet">
    <style>
    * {{ margin:0; padding:0; box-sizing:border-box; }}
    body {{ background:transparent; font-family:'Inter',sans-serif; }}
    .card-bottom {{
        max-width:440px; margin:0 auto;
        background:rgba(15,23,42,0.92);
        backdrop-filter:blur(40px) saturate(1.8);
        border:1px solid rgba(59,130,246,0.15);
        border-radius:0 0 28px 28px;
        border-top:none;
        padding:1rem 2.5rem 2.5rem;
    }}
    .security {{
        display:flex; align-items:center; justify-content:center; gap:8px;
        margin:0.8rem 0 1rem; font-size:0.72rem; color:#475569;
    }}
    .security .dot {{
        width:7px; height:7px; border-radius:50%;
        background:#22c55e; animation:p 2s infinite;
    }}
    @keyframes p {{ 0%,100%{{ opacity:1; }} 50%{{ opacity:0.3; }} }}
    .divider {{
        height:1px; margin:0.3rem 0 1.2rem;
        background:linear-gradient(90deg,transparent,rgba(59,130,246,0.2),transparent);
    }}
    .features {{ display:grid; grid-template-columns:1fr 1fr; gap:10px; }}
    .feat {{
        display:flex; align-items:center; gap:8px;
        padding:0.65rem 0.8rem; border-radius:10px;
        background:rgba(59,130,246,0.04);
        border:1px solid rgba(59,130,246,0.08);
        transition:all 0.2s ease;
    }}
    .feat:hover {{ background:rgba(59,130,246,0.08); border-color:rgba(59,130,246,0.18); }}
    .feat .fi {{ font-size:1.05rem; }}
    .feat .ft {{ font-size:0.72rem; color:#94a3b8; font-weight:500; }}
    .footer {{ text-align:center; margin-top:2rem; }}
    .footer .f1 {{ font-size:0.7rem; color:#334155; font-weight:500; }}
    .footer .f2 {{ font-size:0.6rem; color:#1e293b; margin-top:4px; }}
    </style>
    </head><body>
    <div class="card-bottom">
        <div class="security">
            <span class="dot"></span>
            <span>Connexion sécurisée via OAuth 2.0</span>
        </div>
        <div class="divider"></div>
        <div class="features">
            <div class="feat"><span class="fi">📡</span><span class="ft">IoT Monitoring</span></div>
            <div class="feat"><span class="fi">🤖</span><span class="ft">IA Générative</span></div>
            <div class="feat"><span class="fi">📊</span><span class="ft">Analytics Pro</span></div>
            <div class="feat"><span class="fi">🔧</span><span class="ft">Maintenance</span></div>
        </div>
        <div class="footer">
            <div class="f1">Université de Sousse · Projet Module BD</div>
            <div class="f2">Phase 2 — Compilateur · Automates · IA · {datetime.now().year}</div>
        </div>
    </div>
    </body></html>
    """
    _login_comp.html(bottom_html, height=280, scrolling=False)

    # Show Google OAuth errors
    if st.session_state.google_oauth_error:
        st.error(f"❌ {st.session_state.google_oauth_error}")
        st.session_state.google_oauth_error = None

    return False
