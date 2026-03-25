from __future__ import annotations

import hmac
import os

import streamlit as st


ADMIN_PASSWORD_KEYS = ("RUNYI_ADMIN_PASSWORD", "ADMIN_PASSWORD")


def ensure_auth_state() -> None:
    if "is_admin" not in st.session_state:
        st.session_state["is_admin"] = False
    if "show_login_form" not in st.session_state:
        st.session_state["show_login_form"] = False


def get_admin_password() -> str:
    for key in ADMIN_PASSWORD_KEYS:
        value = os.getenv(key)
        if value:
            return str(value)

    try:
        for key in ADMIN_PASSWORD_KEYS:
            value = st.secrets.get(key)
            if value:
                return str(value)
    except Exception:
        pass

    return ""


def auth_configured() -> bool:
    return bool(get_admin_password())


def is_admin() -> bool:
    ensure_auth_state()
    return bool(st.session_state.get("is_admin", False))


def login(password: str) -> bool:
    ensure_auth_state()
    expected = get_admin_password()
    success = bool(expected) and hmac.compare_digest(password, expected)
    st.session_state["is_admin"] = success
    if success:
        st.session_state["show_login_form"] = False
    return success


def logout() -> None:
    ensure_auth_state()
    st.session_state["is_admin"] = False
    st.session_state["show_login_form"] = False
