from fasthtml.common import *


def user_auth_before(req, sess):
    auth = req.scope['auth'] = sess.get('auth', None)
    if not auth:
        return RedirectResponse('/users/login', status_code=303)


beforeware = Beforeware(
    user_auth_before,
    skip=[r'/favicon\.ico', r'/static/.*', r'.*\.css', r'.*\.js', '/users/login']
)

app, rt = fast_app(before=beforeware)


@rt("/")
def get():
    return Titled("Home")


@rt("/users/login")
def get():
    return Titled("Login")


serve()
