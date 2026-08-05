from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from app.services.email_service import send_contact_email

web_bp = Blueprint("web", __name__)

@web_bp.get("/")
def index():
    return render_template("index.html")

@web_bp.get("/dashboard")
@login_required
def dashboard():
    return render_template("dashboard.html")

@web_bp.get("/portfolio")
@login_required
def portfolio():
    return render_template("portfolio.html")

@web_bp.get("/about")
def about():
    return render_template("about.html")

@web_bp.get("/contact")
def contact():
    return render_template("contact.html")

@web_bp.post("/contact")
def contact_submit():
    name = request.form.get("name", "").strip()
    email = request.form.get("email", "").strip()
    message = request.form.get("message", "").strip()

    if not name or not email or not message:
        flash("Please fill in your name, email, and message.", "error")
        return redirect(url_for("web.contact"))

    try:
        send_contact_email(name=name, email=email, message=message)
        flash("Message sent successfully. We will get back to you soon.", "success")
        return redirect(url_for("web.contact"))
    except Exception:
        flash("Message received, but email sending is not configured on this server yet.", "error")
        return redirect(url_for("web.contact"))