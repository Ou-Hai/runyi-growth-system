from __future__ import annotations

import streamlit as st

from auth import auth_configured, ensure_auth_state, is_admin, login, logout

LANG_OPTIONS = {
    "中文": "zh",
    "English": "en",
    "Deutsch": "de",
}


def t(zh: str, en: str, de: str | None = None) -> str:
    lang = st.session_state.get("lang", "zh")
    if lang == "zh":
        return zh
    if lang == "de":
        return de or en
    return en


def init_sidebar(current_route: str = "home") -> str:
    if "lang" not in st.session_state:
        st.session_state["lang"] = "zh"
    ensure_auth_state()

    top_left, top_mid, top_right = st.columns([0.9, 1.4, 0.7])
    with top_left:
        if current_route != "home":
            st.markdown('<div class="home-chip">', unsafe_allow_html=True)
            if st.button(t("🏠 返回主页", "🏠 Back Home", "🏠 Zurück zur Startseite"), key="go_home_top", use_container_width=True):
                st.session_state["route"] = "home"
                st.rerun()
            st.markdown("</div>", unsafe_allow_html=True)
        else:
            st.write("")
    with top_mid:
        current_label = {
            "zh": "中文",
            "en": "English",
            "de": "Deutsch",
        }.get(st.session_state["lang"], "中文")
        choice = st.segmented_control(
            label=t("语言", "Language", "Sprache"),
            options=list(LANG_OPTIONS.keys()),
            default=current_label,
            key="lang_segmented_control",
            label_visibility="collapsed",
        )
        if choice:
            st.session_state["lang"] = LANG_OPTIONS[choice]
    with top_right:
        if is_admin():
            st.caption(t("管理员模式", "Admin Mode", "Admin-Modus"))
            if st.button(t("退出登录", "Log Out", "Abmelden"), key="logout_admin", use_container_width=True):
                logout()
                st.rerun()
        elif auth_configured():
            if st.session_state.get("show_login_form", False):
                with st.form("admin_login_form", clear_on_submit=True):
                    password = st.text_input(
                        t("管理员密码", "Admin Password", "Admin-Passwort"),
                        type="password",
                        label_visibility="collapsed",
                        placeholder=t("管理员密码", "Admin password", "Admin-Passwort"),
                    )
                    submitted = st.form_submit_button(t("登录", "Log In", "Anmelden"), use_container_width=True)
                if submitted:
                    if login(password):
                        st.rerun()
                    st.error(t("密码不正确。", "Incorrect password.", "Falsches Passwort."))
                if st.button(t("取消", "Cancel", "Abbrechen"), key="cancel_admin_login", use_container_width=True):
                    st.session_state["show_login_form"] = False
                    st.rerun()
            else:
                st.caption(t("只读模式", "Read-Only", "Nur Lesen"))
                if st.button(t("管理员登录", "Admin Login", "Admin-Anmeldung"), key="show_admin_login", use_container_width=True):
                    st.session_state["show_login_form"] = True
                    st.rerun()
        else:
            st.caption(t("只读模式", "Read-Only", "Nur Lesen"))

    return st.session_state["lang"]


def inject_styles() -> None:
    st.markdown(
        """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Baloo+2:wght@400;600;700&family=Noto+Sans+SC:wght@400;500;700&display=swap');

        :root {
            --ink: #24324a;
            --peach: #ff9b72;
            --sun: #ffd86b;
            --mint: #a6e3c4;
            --sky: #b8d8ff;
            --berry: #ff9cc0;
            --cream: #fffaf1;
            --card: rgba(255, 255, 255, 0.9);
            --line: rgba(36, 50, 74, 0.09);
        }

        html, body, [class*="css"] {
            font-family: "Noto Sans SC", "Baloo 2", sans-serif;
            color: var(--ink);
        }

        .stApp {
            background:
                radial-gradient(circle at 15% 20%, rgba(255, 216, 107, 0.26), transparent 22%),
                radial-gradient(circle at 85% 18%, rgba(255, 156, 192, 0.18), transparent 18%),
                radial-gradient(circle at 18% 84%, rgba(166, 227, 196, 0.24), transparent 22%),
                radial-gradient(circle at 82% 82%, rgba(184, 216, 255, 0.22), transparent 20%),
                linear-gradient(180deg, #fff7ec 0%, #fffdfa 54%, #f7fbff 100%);
        }

        .block-container {
            padding-top: 1.2rem;
            padding-bottom: 2rem;
            max-width: 1180px;
        }

        [data-testid="stSidebar"],
        [data-testid="stSidebarNav"],
        [data-testid="collapsedControl"],
        [data-testid="stHeader"],
        [data-testid="stToolbar"] {
            display: none !important;
        }

        [data-testid="stMetric"] {
            background: rgba(255,255,255,0.86);
            border: 1px solid var(--line);
            border-radius: 22px;
            padding: 16px 18px;
            box-shadow: 0 14px 28px rgba(255, 155, 114, 0.1);
        }

        .hero-card {
            position: relative;
            overflow: hidden;
            padding: 30px 30px 28px;
            border-radius: 34px;
            background:
                radial-gradient(circle at top right, rgba(255,255,255,0.26), transparent 24%),
                radial-gradient(circle at left bottom, rgba(255,255,255,0.16), transparent 20%),
                linear-gradient(135deg, rgba(255, 155, 114, 0.95), rgba(255, 216, 107, 0.92));
            color: white;
            box-shadow: 0 24px 48px rgba(255, 155, 114, 0.2);
            margin-bottom: 20px;
        }

        .hero-card.home-hero {
            background:
                radial-gradient(circle at 18% 24%, rgba(255,255,255,0.72), transparent 16%),
                radial-gradient(circle at 82% 22%, rgba(184, 216, 255, 0.42), transparent 18%),
                radial-gradient(circle at 18% 82%, rgba(166, 227, 196, 0.36), transparent 18%),
                linear-gradient(180deg, rgba(255,255,255,0.84), rgba(249,250,255,0.84));
            color: var(--ink);
            box-shadow: 0 18px 42px rgba(184, 216, 255, 0.16);
            border: 1px solid rgba(36, 50, 74, 0.06);
        }

        .hero-card.home-hero h1,
        .hero-card.home-hero h2,
        .hero-card.home-hero h3,
        .hero-card.home-hero p {
            color: var(--ink);
        }

        .hero-card.home-hero::before {
            content: "☁️";
            animation: floatCloud 5s ease-in-out infinite;
        }

        .hero-card.home-hero::after {
            content: "✨";
            right: 40px;
            bottom: 22px;
            animation: twinkle 2.4s ease-in-out infinite;
        }

        .hero-card::before {
            content: "☁️";
            position: absolute;
            right: 28px;
            top: 18px;
            font-size: 2.1rem;
            opacity: 0.92;
        }

        .hero-card::after {
            content: "⭐";
            position: absolute;
            right: 72px;
            bottom: 18px;
            font-size: 1.6rem;
            opacity: 0.95;
        }

        .hero-card h1, .hero-card h2, .hero-card h3, .hero-card p {
            color: white;
            margin: 0;
        }

        .soft-card {
            background: var(--card);
            border: 1px solid var(--line);
            border-radius: 24px;
            padding: 18px 20px;
            box-shadow: 0 12px 24px rgba(184, 216, 255, 0.12);
            margin-bottom: 14px;
        }

        .play-card {
            min-height: 180px;
            background:
                radial-gradient(circle at top right, rgba(255,255,255,0.45), transparent 26%),
                linear-gradient(180deg, rgba(255,255,255,0.98), rgba(255,250,242,0.99));
            border: 1px solid rgba(36, 50, 74, 0.08);
            border-radius: 26px;
            padding: 20px 20px 18px;
            box-shadow: 0 16px 34px rgba(36, 50, 74, 0.08);
            margin-bottom: 14px;
        }

        .record-card {
            background: linear-gradient(180deg, rgba(255,255,255,0.98), rgba(255,250,242,0.98));
            border: 1px solid rgba(36, 50, 74, 0.08);
            border-radius: 22px;
            padding: 16px 18px;
            box-shadow: 0 10px 22px rgba(36, 50, 74, 0.08);
            margin-bottom: 12px;
        }

        .record-card-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            gap: 10px;
            margin-bottom: 12px;
        }

        .record-card-title {
            font-size: 1.02rem;
            font-weight: 700;
        }

        .record-pill {
            display: inline-flex;
            align-items: center;
            border-radius: 999px;
            padding: 5px 10px;
            font-size: 0.86rem;
            font-weight: 700;
            background: rgba(255, 216, 107, 0.2);
            color: var(--ink);
        }

        .record-grid {
            display: grid;
            grid-template-columns: repeat(2, minmax(0, 1fr));
            gap: 10px 14px;
        }

        .record-cell-label {
            font-size: 0.82rem;
            opacity: 0.72;
            margin-bottom: 3px;
        }

        .record-cell-value {
            font-size: 0.96rem;
            font-weight: 600;
            word-break: break-word;
        }

        .mobile-note {
            margin: 8px 0 12px 0;
            font-size: 0.9rem;
            opacity: 0.72;
        }

        .celebration-card {
            border-radius: 24px;
            padding: 20px 22px;
            background: linear-gradient(135deg, rgba(184, 216, 255, 0.25), rgba(166, 227, 196, 0.28));
            border: 1px dashed rgba(36, 50, 74, 0.14);
        }

        .pill-row {
            display: flex;
            gap: 10px;
            flex-wrap: wrap;
            margin-top: 12px;
        }

        .pill {
            padding: 8px 12px;
            border-radius: 999px;
            background: rgba(255, 255, 255, 0.24);
            border: 1px solid rgba(255, 255, 255, 0.28);
            font-size: 0.95rem;
        }

        .map-panel {
            background:
                radial-gradient(circle at top left, rgba(255,255,255,0.52), transparent 20%),
                linear-gradient(180deg, rgba(255,255,255,0.45), rgba(255,255,255,0.18));
            border: 1px dashed rgba(36, 50, 74, 0.12);
            border-radius: 30px;
            padding: 22px 22px 14px;
            margin-top: 6px;
        }

        .map-title {
            font-size: 1.35rem;
            font-weight: 700;
            margin-bottom: 14px;
            color: var(--ink);
        }

        .stButton > button {
            border-radius: 999px;
            border: none;
            background: linear-gradient(135deg, #ff8f67, #ffb574);
            color: white;
            font-weight: 700;
            padding: 0.56rem 1rem;
            box-shadow: 0 10px 18px rgba(255, 143, 103, 0.16);
        }

        .stButton > button:hover {
            filter: brightness(1.03);
            transform: translateY(-1px);
        }

        .home-chip button {
            background: linear-gradient(180deg, rgba(255,255,255,0.96), rgba(255,250,242,0.96));
            color: var(--ink);
            border: 1px solid rgba(36, 50, 74, 0.08);
            box-shadow: 0 8px 18px rgba(36, 50, 74, 0.08);
        }

        .home-chip button:hover {
            box-shadow: 0 12px 22px rgba(184, 216, 255, 0.16);
        }

        .map-card button {
            width: 100%;
            min-height: 214px;
            border-radius: 28px;
            border: 1px solid rgba(36, 50, 74, 0.08);
            background:
                radial-gradient(circle at top right, rgba(255, 216, 107, 0.2), transparent 25%),
                radial-gradient(circle at left bottom, rgba(184, 216, 255, 0.18), transparent 22%),
                linear-gradient(180deg, rgba(255,255,255,0.98), rgba(255,250,242,0.99));
            color: var(--ink);
            box-shadow: 0 18px 34px rgba(36, 50, 74, 0.08);
            text-align: left;
            justify-content: flex-start;
            white-space: break-spaces;
            padding: 22px 22px 18px;
        }

        .map-card button p {
            color: var(--ink);
            font-size: 1.18rem;
            line-height: 1.65;
            font-weight: 700;
            white-space: break-spaces;
        }

        .home-scene {
            position: relative;
            min-height: 132px;
            margin: 6px 0 14px 0;
        }

        .float-item {
            position: absolute;
            font-size: 2rem;
            filter: drop-shadow(0 8px 14px rgba(36, 50, 74, 0.08));
            animation: bob 4.8s ease-in-out infinite;
        }

        .float-a { left: 8%; top: 10px; animation-delay: 0s; }
        .float-b { left: 34%; top: 54px; animation-delay: 0.8s; }
        .float-c { left: 58%; top: 18px; animation-delay: 1.2s; }
        .float-d { left: 80%; top: 60px; animation-delay: 1.8s; }

        @keyframes bob {
            0%, 100% { transform: translateY(0px) rotate(0deg); }
            50% { transform: translateY(-10px) rotate(2deg); }
        }

        @keyframes floatCloud {
            0%, 100% { transform: translateY(0px); }
            50% { transform: translateY(-8px); }
        }

        @keyframes twinkle {
            0%, 100% { opacity: 0.75; transform: scale(1); }
            50% { opacity: 1; transform: scale(1.15); }
        }

        div[data-testid="stProgress"] > div > div {
            background: linear-gradient(90deg, #ff8f67 0%, #ffd86b 52%, #a6e3c4 100%);
        }

        @media (max-width: 900px) {
            .block-container {
                padding-top: 0.55rem;
                padding-left: 0.72rem;
                padding-right: 0.72rem;
                padding-bottom: 1rem;
            }

            .hero-card {
                padding: 18px 16px 16px;
                border-radius: 24px;
                margin-bottom: 14px;
            }

            .hero-card::before {
                right: 18px;
                top: 14px;
                font-size: 1.7rem;
            }

            .hero-card::after {
                right: 50px;
                bottom: 12px;
                font-size: 1.2rem;
            }

            .map-panel {
                padding: 14px 12px 4px;
                border-radius: 20px;
            }

            .map-card button {
                min-height: 126px;
                border-radius: 18px;
                padding: 14px 12px 11px;
            }

            .map-card button p {
                font-size: 0.95rem;
                line-height: 1.36;
            }

            .play-card,
            .soft-card,
            .celebration-card,
            [data-testid="stMetric"] {
                border-radius: 18px;
                padding: 12px 13px;
                margin-bottom: 10px;
            }

            .pill-row {
                gap: 6px;
                margin-top: 8px;
            }

            .pill {
                font-size: 0.8rem;
                padding: 6px 9px;
            }

            .home-scene {
                min-height: 74px;
                margin: 2px 0 8px 0;
            }

            .float-item {
                font-size: 1.32rem;
            }

            .record-grid {
                grid-template-columns: 1fr;
                gap: 8px;
            }

            [data-testid="stHorizontalBlock"] {
                gap: 0.5rem;
            }

            [data-testid="column"] {
                width: 100% !important;
                flex: 1 1 100% !important;
            }

            .stButton > button {
                min-height: 2.55rem;
                font-size: 0.96rem;
            }

            .map-title {
                font-size: 1.16rem;
                margin-bottom: 8px;
            }

            .record-card {
                padding: 12px 13px;
                margin-bottom: 8px;
                border-radius: 18px;
            }

            .record-card-header {
                margin-bottom: 8px;
                gap: 8px;
            }

            .record-card-title {
                font-size: 0.96rem;
            }

            .record-pill {
                padding: 4px 8px;
                font-size: 0.78rem;
            }

            .record-cell-label {
                font-size: 0.76rem;
                margin-bottom: 2px;
            }

            .record-cell-value {
                font-size: 0.9rem;
            }

            h1, h2, h3 {
                margin-bottom: 0.2rem;
            }

            p {
                margin-bottom: 0.35rem;
            }

            [data-testid="stTabs"] {
                margin-top: 0.2rem;
            }

            [data-testid="stMarkdownContainer"] hr {
                margin: 0.65rem 0;
            }

            [data-testid="stAlert"] {
                padding: 0.55rem 0.7rem;
                border-radius: 16px;
            }

            div[data-testid="stProgress"] {
                margin: 0.3rem 0 0.55rem 0;
            }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_hero(title: str, subtitle: str, pills: list[str] | None = None, variant: str = "default") -> None:
    pills = pills or []
    pills_html = "".join(f'<span class="pill">{item}</span>' for item in pills)
    hero_class = "hero-card home-hero" if variant == "home" else "hero-card"
    subtitle_html = f'<p style="margin-top:12px;font-size:1.05rem;opacity:0.97;">{subtitle}</p>' if subtitle else ""
    st.markdown(
        f"""
        <div class="{hero_class}">
            <h2>{title}</h2>
            {subtitle_html}
            <div class="pill-row">{pills_html}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_home_scene() -> None:
    st.markdown(
        """
        <div class="home-scene">
            <div class="float-item float-a">☁️</div>
            <div class="float-item float-b">🍭</div>
            <div class="float-item float-c">⭐</div>
            <div class="float-item float-d">🧸</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
