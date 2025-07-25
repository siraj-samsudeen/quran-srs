from fasthtml.common import *
from monsterui.all import *
from utils import get_database_connection
from datetime import datetime
from dataclasses import dataclass

# Import database connection and tables from main module context
# These will be passed in when the router is created

@dataclass
class Login:
    email: str
    password: str

OPTION_MAP = {
    "age_group": ["child", "teen", "adult"],
    "relationship": ["self", "parent", "teacher", "sibling"],
}


db = get_database_connection()

users = db.t.users
hafizs = db.t.hafizs
hafizs_users = db.t.hafizs_users
revisions = db.t.revisions

(Hafiz, User, Hafiz_Users, Revisions) = (
    hafizs.dataclass(),
    users.dataclass(),
    hafizs_users.dataclass(),
    revisions.dataclass(),
)

# Redirect target for login failures
login_redir = RedirectResponse("/users/login", status_code=303)

users_app, rt = fast_app(hdrs=Theme.blue.headers())

@rt("/login")
def get(sess):
    """Display login form"""
    form = Form(
        LabelInput(label="Email", name="email", type="email"),
        LabelInput(label="Password", name="password", type="password"),
        Button("Login"),
        action="/users/login",
        method="post",
    )
    return Titled("Login", form)

@rt("/login")
def post(login: Login, sess):
    """Process login form submission"""
    if not login.email or not login.password:
        return login_redir
    try:
        u = users(where="email = '{}'".format(login.email))[0]
    except IndexError:
        return login_redir
    if not compare_digest(u.password.encode("utf-8"), login.password.encode("utf-8")):
        return login_redir
    sess["user_auth"] = u.id
    hafizs_users.xtra(id=u.id)
    return RedirectResponse("/users/hafiz_selection", status_code=303)

@rt("/logout")
def get(sess):
    """Logout user and clear session"""
    user_auth = sess.get("user_auth", None)
    if user_auth is not None:
        del sess["user_auth"]
    auth = sess.get("auth", None)
    if auth is not None:
        del sess["auth"]
    return RedirectResponse("/users/login", status_code=303)

@rt("/hafiz_selection")
def get(sess):
    """Display hafiz selection page"""
    # Reset xtra attributes to show data for all hafiz
    revisions.xtra()
    hafizs_users.xtra()
    auth = sess.get("auth", None)
    user_auth = sess.get("user_auth", None)
    if user_auth is None:
        return login_redir

    cards = [
        render_hafiz_card(h, auth) for h in hafizs_users() if h.user_id == user_auth
    ]

    def render_options(option):
        return Option(
            option.capitalize(),
            value=option,
        )

    hafiz_form = Card(
        Titled(
            "Add Hafiz",
            Form(
                LabelInput(label="Name", name="name"),
                LabelSelect(
                    *map(render_options, OPTION_MAP["age_group"]),
                    label="Age Group",
                    name="age_group",
                ),
                LabelInput(
                    label="Daily Capacity",
                    name="daily_capacity",
                    type="number",
                    min="1",
                    value="1",
                    required=True,
                ),
                LabelSelect(
                    *map(render_options, OPTION_MAP["relationship"]),
                    label="Relationship",
                    name="relationship",
                ),
                Button("Add Hafiz"),
                action="/users/add_hafiz",
                method="post",
            ),
        ),
        cls="w-[300px]",
    )

    return Titled(
        "Hafiz Selection",
        Container(
            Div(
                Div(*cards, cls=(FlexT.block, FlexT.wrap, "gap-4")),
                hafiz_form,
                cls="space-y-4",
            )
        ),
    )

@rt("/hafiz_selection")
def post(current_hafiz_id: int, sess):
    """Switch to selected hafiz account"""
    sess["auth"] = current_hafiz_id
    return RedirectResponse("/", status_code=303)

@rt("/add_hafiz")
def post(hafiz: Hafiz, relationship: str, sess):
    """Add new hafiz and create user relationship"""
    hafiz_id = hafizs.insert(hafiz)
    hafizs_users.insert(
        hafiz_id=hafiz_id.id,
        user_id=sess["user_auth"],
        relationship=relationship,
        granted_by_user_id=sess["user_auth"],
        granted_at=datetime.now().strftime("%d-%m-%y %H:%M:%S"),
    )
    return RedirectResponse("/users/hafiz_selection", status_code=303)

def render_hafiz_card(hafizs_user, auth):
    """Render individual hafiz selection card"""
    is_current_hafizs_user = auth != hafizs_user.hafiz_id
    return Card(
        header=DivFullySpaced(H3(hafizs[hafizs_user.hafiz_id].name)),
        footer=Button(
            "Switch Hafiz" if is_current_hafizs_user else "Go to home",
            name="current_hafiz_id",
            value=hafizs_user.hafiz_id,
            hx_post="/users/hafiz_selection",
            hx_target="body",
            hx_replace_url="true",
            cls=ButtonT.primary,
        ),
        cls="min-w-[300px] max-w-[400px]",
    )