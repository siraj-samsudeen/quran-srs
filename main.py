from fasthtml.common import *
from monsterui.all import *


def user_auth_before(req, sess):
    auth = req.scope["auth"] = sess.get("auth", None)
    if not auth:
        return RedirectResponse("/users/login", status_code=303)


beforeware = Beforeware(
    user_auth_before,
    skip=[
        r"/favicon\.ico",
        r"/static/.*",
        r".*\.css",
        r".*\.js",
        "/users/login",
        "/users/signup",
    ],
)

app, rt = fast_app(before=beforeware, hdrs=Theme.blue.headers())


@rt("/")
def get():
    return Titled("Home")


@rt("/users/login")
def get():
    return Titled("Login")


@rt("/users/signup")
def get():
    return Titled(
        "User Registration",
        Form(
            LabelInput("Name", required=True),
            LabelInput("Email", type="email", required=True),
            LabelInput("Password", type="password", required=True),
            LabelInput(
                "Confirm Password",
                name="confirm_password",
                type="password",
                required=True,
            ),
            Button("Signup", cls=ButtonT.primary),
            action="/users/signup",
            method="post",
        ),
        P(
            "Already have an account? ",
            A("Login", href="/users/login", cls=TextT.primary),
            cls="mt-4",
        ),
        cls="space-y-6",
    )


serve()
