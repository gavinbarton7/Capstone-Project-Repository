"""The HTML pages (sign up, login, dashboard, profile, ...).

This file is the ONLY part of the backend that serves web pages. It exists so the
backend can be tried on its own, without the React frontend:

    python app.py   ->   open http://127.0.0.1:8000

The pages are plain HTML files in the /templates folder. They sign in through the
same sessions as the React frontend and save through the same /api/... endpoints
(auth.py, profile_routes.py, settings_routes.py, budget_routes.py).

If you only want the API (for example next to the React app) set the environment
variable SERVE_HTML_PAGES=0 and none of the routes below are created. See app.py.
"""

from flask import Blueprint, redirect, render_template, request, url_for

from auth import (
    check_credentials,
    create_account,
    current_user,
    end_session,
    login_required,
    login,
    register,
    set_session_cookie,
    start_session,
)
from settings_routes import current_settings, format_date, settings_options_for_templates
from validation import pick

pages_bp = Blueprint("pages", __name__)

# ---- HTML template filenames (inside the /templates folder) ------------------
# Rename these when the real page names are known; nothing else needs to change.
SIGNUP_TEMPLATE = "signup.html"
LOGIN_TEMPLATE = "login.html"
DASHBOARD_TEMPLATE = "dashboard.html"
BUDGET_TEMPLATE = "budget.html"
PROFILE_TEMPLATE = "profile.html"
SETTING_TEMPLATE = "setting.html"
EXPENSES_TEMPLATE = "expenses.html"

# ---- Form field names (the name="..." on each <input>) ------------------------
# Sign up form:  first_name, last_name, email, password
# Login form:    email, password, remember_me (optional checkbox)
# Change a string below only if the HTML uses a different name.
FIELD_FIRST_NAME = "first_name"
FIELD_LAST_NAME = "last_name"
FIELD_EMAIL = "email"
FIELD_REMEMBER_ME = "remember_me"


# Make a date show in the user's chosen format inside any template:
#     {{ user.created_at | fmt_date }}
pages_bp.add_app_template_filter(format_date, "fmt_date")


@pages_bp.context_processor
def template_variables():
    """Variables every page can use without the route passing them in.

      {{ user.first_name }} {{ user.last_name }} {{ user.email }} {{ user.phone }} ...
          the signed-in user (empty on the login and sign up pages)
      {{ settings.date_format }} {{ settings.language }} {{ settings.week_start }}
          the user's settings, and {{ settings.options }} for building dropdowns
    """
    return {
        "user": current_user(),
        "settings": {**current_settings(), "options": settings_options_for_templates()},
    }


# =============================================================================
# Public pages: sign up, login, logout
# =============================================================================
@pages_bp.route("/")
def home():
    if current_user():
        return redirect(url_for("pages.dashboard"))
    return render_template(SIGNUP_TEMPLATE)


@pages_bp.route("/signup", methods=["GET", "POST"])
def signup():
    """Sign up page. The HTML form POSTs here: action="{{ url_for('pages.signup') }}"

    On a problem the page is shown again with `error` (text) and `form` (what they
    typed, without the password) so the inputs can be refilled:
        {% if error %}<p>{{ error }}</p>{% endif %}
        <input name="first_name" value="{{ form.first_name if form }}">
    On success they are sent to the login page (they are NOT signed in yet).
    """
    if request.method == "GET":
        return render_template(SIGNUP_TEMPLATE)

    if request.is_json:               # same as POST /api/auth/register
        return register()

    data = request.form.to_dict()
    user, error, status = create_account(data)
    if error:
        form = {
            FIELD_FIRST_NAME: data.get(FIELD_FIRST_NAME, ""),
            FIELD_LAST_NAME: data.get(FIELD_LAST_NAME, ""),
            FIELD_EMAIL: data.get(FIELD_EMAIL, ""),
        }
        return render_template(SIGNUP_TEMPLATE, error=error, form=form), status
    return redirect(url_for("pages.login_page", created=1))


@pages_bp.route("/login", methods=["GET", "POST"])
def login_page():
    """Login page. The HTML form POSTs here: action="{{ url_for('pages.login_page') }}"

    A wrong email OR password shows the page again with `error` and `form.email`.
    Success: the sign-in cookie is set and they go to the dashboard.
    """
    if request.method == "GET":
        if current_user():
            return redirect(url_for("pages.dashboard"))
        # /login?created=1 is where sign up sends people after "Create"
        message = "Account created! Please log in." if request.args.get("created") else None
        return render_template(LOGIN_TEMPLATE, message=message)

    if request.is_json:               # same as POST /api/auth/login
        return login()

    data = request.form.to_dict()
    email = (pick(data, FIELD_EMAIL, default="") or "").strip().lower()
    user = check_credentials(email, pick(data, "password"))
    if user is None:
        # Same message whether the email or the password is wrong, so the form can't
        # be used to find out which emails have accounts.
        return render_template(
            LOGIN_TEMPLATE, error="Incorrect email or password.", form={FIELD_EMAIL: email}
        ), 401

    remember_me = data.get(FIELD_REMEMBER_ME) in ("on", "true", "1")
    token = start_session(user["user_id"], remember_me)
    return set_session_cookie(redirect(url_for("pages.dashboard")), token, remember_me)


@pages_bp.route("/logout", methods=["GET", "POST"])
def logout_page():
    """Every page's 'Log out' link points here: href="/logout"."""
    return end_session(redirect(url_for("pages.home")))


# =============================================================================
# Pages for signed-in users (@login_required sends everyone else to /login)
# =============================================================================
@pages_bp.route("/dashboard")
@login_required
def dashboard():
    return render_template(DASHBOARD_TEMPLATE)


@pages_bp.route("/budget")
@login_required
def budget():
    return render_template(BUDGET_TEMPLATE)


@pages_bp.route("/profile")
@login_required
def profile():
    return render_template(PROFILE_TEMPLATE)


@pages_bp.route("/setting")
@login_required
def setting():
    return render_template(SETTING_TEMPLATE)


@pages_bp.route("/expenses")
@login_required
def expenses():
    return render_template(EXPENSES_TEMPLATE)
