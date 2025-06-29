from flask import Flask, request, render_template, redirect, flash, url_for, jsonify, abort

from supabase import create_client, Client

SUPABASE_URL = "https://eqytjxqghcylmvscqqvd.supabase.co"
SUPEBASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImVxeXRqeHFnaGN5bG12c2NxcXZkIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTEwNjI5NDMsImV4cCI6MjA2NjYzODk0M30.eXFvI8T-2VtjoIoUKy2UHzrgjdmAPQPgJFzshmBYgBI"

supabase: Client = create_client(SUPABASE_URL, SUPEBASE_KEY)

app = Flask(__name__)
app.secret_key = "heinerkacesecretcode"

#Route to show tasks

@app.route("/")
def index():
    response = supabase.table("tasks").select("*").execute()
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
@app.route("/add-task", methods=["POST"])
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
        "status": status
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
def delete_task(task_id):
    supabase.table("tasks").delete().eq("task_id", task_id).execute()
    flash("Task deleted.", "info")
    return redirect(url_for("index"))

# === Run the app ===
if __name__ == "__main__":
    print("Starting")
    app.run(debug=True)