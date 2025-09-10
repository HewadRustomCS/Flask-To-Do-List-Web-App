#!/usr/bin/env python3
from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import os

app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev-secret")
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///todo.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)

class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(140), nullable=False)
    priority = db.Column(db.String(10), default="med")  # low/med/high
    due = db.Column(db.String(10), nullable=True)       # YYYY-MM-DD
    done = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<Task {self.id} {self.title[:20]!r}>"

@app.route("/", methods=["GET"])
def index():
    show = request.args.get("show", "open")  # open|all
    if show == "all":
        tasks = Task.query.order_by(Task.done.asc(), Task.created_at.desc()).all()
    else:
        tasks = Task.query.filter_by(done=False).order_by(Task.created_at.desc()).all()
    counts = {
        "total": Task.query.count(),
        "open": Task.query.filter_by(done=False).count(),
        "done": Task.query.filter_by(done=True).count()
    }
    return render_template("index.html", tasks=tasks, show=show, counts=counts)

@app.route("/add", methods=["POST"])
def add():
    title = request.form.get("title", "").strip()
    priority = request.form.get("priority", "med")
    due = request.form.get("due", "").strip()
    if not title:
        flash("Title cannot be empty.", "error")
        return redirect(url_for("index"))
    task = Task(title=title, priority=priority, due=due or None)
    db.session.add(task)
    db.session.commit()
    flash("Task added ✅", "success")
    return redirect(url_for("index"))

@app.route("/toggle/<int:task_id>", methods=["POST"])
def toggle(task_id):
    task = Task.query.get_or_404(task_id)
    task.done = not task.done
    db.session.commit()
    flash(("Marked done ✅" if task.done else "Reopened 🔁"), "info")
    return redirect(url_for("index", show=request.args.get("show", "open")))

@app.route("/delete/<int:task_id>", methods=["POST"])
def delete(task_id):
    task = Task.query.get_or_404(task_id)
    db.session.delete(task)
    db.session.commit()
    flash("Task deleted 🗑️", "warning")
    return redirect(url_for("index", show=request.args.get("show", "open")))

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)
