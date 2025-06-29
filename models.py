class User(UserMixin):
    def __init__(self, user_id, username):
        self.id = user_id
        self.username = username

@login_manager.user_loader
def load_user(user_id):
    user = db.execute("SELECT * FROM users WHERE user_id = %s", (user_id,)).fetchone()
    if user:
        return User(user["user_id"], user["username"])
    return None
