from fasthtml.common import *
from monsterui.all import *
from database import users, hafizs, revisions, hafizs_items, plans

# DaisyUI (Tailwind component library)
daisyui_css = Link(
    rel="stylesheet",
    href="https://cdn.jsdelivr.net/npm/daisyui@4.12.14/dist/full.min.css",
)
# Tabulator
tabulator_css = Link(
    rel="stylesheet",
    href="https://unpkg.com/tabulator-tables@6.3.0/dist/css/tabulator_semanticui.min.css",
)
tabulator_js = Script(src="https://unpkg.com/tabulator-tables@6.3.0/dist/js/tabulator.min.js")
style_css = Link(rel="stylesheet", href="/public/css/style.css")
favicon = Link(rel="icon", type="image/svg+xml", href="/public/favicon.svg")
hyperscript_header = Script(src="https://unpkg.com/hyperscript.org@0.9.14")
alpinejs_header = Script(
    src="https://cdn.jsdelivr.net/npm/alpinejs@3.x.x/dist/cdn.min.js", defer=True
)

def user_auth(req, sess):
    # Check user authentication
    user_id = req.scope["user_auth"] = sess.get("user_auth", None)
    if user_id:
        try:
            users[user_id]
        except NotFoundError:
            del sess["user_auth"]
            user_id = None
    if not user_id:
        return RedirectResponse("/users/login", status_code=303)

user_bware = Beforeware(
    user_auth,
    skip=["/users/login", "/users/logout", "/users/signup"],
)

def hafiz_auth(req, sess):
    # Check hafiz authentication
    hafiz_id = req.scope["auth"] = sess.get("auth", None)
    if hafiz_id:
        try:
            hafizs[hafiz_id]
        except NotFoundError:
            del sess["auth"]
            hafiz_id = None
    if not hafiz_id:
        return RedirectResponse("/hafiz/selection", status_code=303)

    revisions.xtra(hafiz_id=hafiz_id)
    hafizs_items.xtra(hafiz_id=hafiz_id)
    plans.xtra(hafiz_id=hafiz_id)

hafiz_bware = Beforeware(
    hafiz_auth,
    skip=[
        "/users/login",
        "/users/logout",
        "/users/signup",
        r"/users/delete/\d+$",
        "/users/account",
        "/hafiz/selection",
        "/hafiz/add",
    ],
)

def create_app_with_auth(**kwargs):
    app, rt = fast_app(
        before=[user_bware, hafiz_bware],
        hdrs=(
            Theme.blue.headers(),
            daisyui_css,
            tabulator_css,
            tabulator_js,
            hyperscript_header,
            alpinejs_header,
            style_css,
            favicon,
        ),
        bodykw={"hx-boost": "true"},
        **kwargs,
    )
    setup_toasts(app)
    return app, rt
