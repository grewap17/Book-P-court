import os

from flask import Flask, render_template, request
from booking import book_court

app = Flask(__name__)


@app.get("/")
def index():
	return render_template("index.html")


@app.post("/book")
def book():
	day = request.form.get("day", "").strip()
	court_number = request.form.get("court_number", "").strip()
	time_str = request.form.get("time", "").strip()
	email = request.form.get("email", "").strip()
	password = request.form.get("password", "").strip()
	headless = request.form.get("headless") == "on"

	# Basic validation
	errors = []
	if not day:
		errors.append("Day is required")
	if not court_number.isdigit():
		errors.append("Court number must be a number")
	if not time_str:
		errors.append("Time is required")
	if not email:
		errors.append("Email is required")
	if not password:
		errors.append("Password is required")

	if errors:
		return render_template("index.html", errors=errors, form=request.form)

	court_name = f"Pickleball Court {int(court_number)}"
	status = book_court(day=day, court_name=court_name, time_str=time_str, email=email, password=password, headless=headless)
	return render_template("result.html", status=status)


if __name__ == "__main__":
	port = int(os.environ.get("PORT", "5000"))
	debug = os.environ.get("FLASK_DEBUG", "").lower() in {"1", "true", "yes", "on"}
	app.run(host="0.0.0.0", port=port, debug=debug)
