from flask import Flask, request, render_template, redirect, flash, url_for, jsonify, abort
from flask_login import LoginManager, login_user, login_required, logout_user, current_user, UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from supabase import create_client, Client
import os

app = Flask(__name__)
app.secret_key = "heinerkacesecretcode"

SUPABASE_URL = "https://eqytjxqghcylmvscqqvd.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImVxeXRqeHFnaGN5bG12c2NxcXZkIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTEwNjI5NDMsImV4cCI6MjA2NjYzODk0M30.eXFvI8T-2VtjoIoUKy2UHzrgjdmAPQPgJFzshmBYgBI"
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

class User(UserMixin):
    def __init__(self, user_id, username):
        self.id = user_id
        self.username = username

@login_manager.user_loader
def load_user(user_id):
    user_query = supabase.table("users").select("*").eq("user_id", int(user_id)).execute()
    user_data = user_query.data[0] if user_query.data else None
    if user_data:
        return User(user_data["user_id"], user_data["username"])
    return None




@app.route("/logout")
@login_required
def logout():
    logout_user()
    flash("You have been logged out.", "info")
    return redirect(url_for("login"))






#Register Users

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"]
        password = generate_password_hash(request.form["password"])

        # Check if user already exists
        existing = supabase.table("users").select("*").eq("username", username).execute()
        if existing.data:
            flash("Username already taken.", "error")
            return redirect(url_for("register"))

        # Insert new user
        supabase.table("users").insert({
            "username": username,
            "password_hash": password
        }).execute()

        flash("Registration successful. Please log in.", "success")
        return redirect(url_for("login"))

    return render_template("register.html")

#Login
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        user_query = supabase.table("users").select("*").eq("username", username).execute()
        user_data = user_query.data[0] if user_query.data else None

        if user_data and check_password_hash(user_data["password_hash"], password):
            user = User(user_data["user_id"], user_data["username"])
            login_user(user)
            return redirect(url_for("index"))
        else:
            flash("Invalid credentials.", "error")

    return render_template("login.html")



#Route to show tasks

@app.route("/")
@login_required
def index():
    response = supabase.table("tasks").select("*").eq("user_id", current_user.id).execute()

    tasks = response.data if response.data else []

    print("Fetched tasks:", tasks)

    # Initialize dictionary
    grouped_tasks = {
        "To Do": [],
        "In Progress": [],
        "Done": []
    }

    for task in tasks:
        status = task.get("status", "To Do")  # Default to "To Do" if missing
        print(f"Processing task: {task['title']} with status: {status}")
        if status in grouped_tasks:
            grouped_tasks[status].append(task)
        else:
            # Optional: Add unknown statuses dynamically
            grouped_tasks.setdefault(status, []).append(task)

    print("Final grouped_tasks:", grouped_tasks)

    return render_template("index.html", grouped_tasks=grouped_tasks)


# === Route: Add a new task ===
from flask_login import login_required, current_user

@app.route("/add-task", methods=["POST"])
@login_required
def add_task_ajax():
    data = request.get_json()
    title = data.get("title", "").strip()
    description = data.get("description", "")
    status = data.get("status", "To Do")

    if not title:
        return jsonify(success=False, message="Title is required.")

    result = supabase.table("tasks").insert({
        "title": title,
        "description": description,
        "status": status,
        "user_id": current_user.id  # 🧠 ownership
    }).execute()

    if result.data:
        return jsonify(success=True)
    else:
        return jsonify(success=False, message="Failed to insert.")



# === Route: Edit a task ===


@app.route("/edit-task-inline/<int:task_id>", methods=["POST"])
def edit_task_inline(task_id):
    
    try:
        response = supabase.table("tasks").select("*").eq("task_id", task_id).execute()
        task = response.data[0] if response.data else None
        if task["user_id"] != current_user.id:
            return jsonify({"success": False, "error": "Unauthorized"}), 403

        if not task:
            return jsonify({"success": False, "error": "Task not found."}), 404

        if not request.is_json:
            return jsonify({"success": False, "error": "Invalid content type, expected JSON."}), 400

        data = request.get_json()

        title = data.get("title")
        if title is None or title.strip() == "":
            title = task.get("title", "")
        else:
            title = title.strip()

        description = data.get("description")
        if description is None:
            description = task.get("description", "")
        else:
            description = description.strip()

        status = (data.get("status") or task.get("status", "To Do")).strip()

        if not title:
            return jsonify({"success": False, "error": "Title is required."}), 400

        updated_task = {
            "title": title,
            "description": description,
            "status": status
        }

        result = supabase.table("tasks").update(updated_task).eq("task_id", task_id).execute()

        if result.data:
            return jsonify({"success": True})
        else:
            return jsonify({"success": False, "error": "Failed to update task."}), 500

    except Exception as e:
        # You might want to log the error here
        return jsonify({"success": False, "error": f"Server error: {str(e)}"}), 500






# === Route: Delete a task (optional) ===
@app.route("/delete/<int:task_id>")
@login_required
def delete_task(task_id):
    task_response = supabase.table("tasks").select("*").eq("task_id", task_id).execute()
    task = task_response.data[0] if task_response.data else None

    if not task:
        flash("Task not found.", "error")
        return redirect(url_for("index"))

    if task["user_id"] != current_user.id:
        abort(403)

    supabase.table("tasks").delete().eq("task_id", task_id).execute()
    flash("Task deleted.", "info")
    return redirect(url_for("index"))


# === Run the app ===
if __name__ == "__main__":
    print("Starting")
    import os
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)