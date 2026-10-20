from flask import Flask, render_template, redirect, url_for

app = Flask(__name__)

## / to redirect to main or signup html page
@app.route("/")
def signup():
    return render_template("signup.html")

## for signup html. Login button there to redirect to dashboard
@app.route("/login", methods=["POST"])
def login():
    # No real authentication yet, just go straight to the dashboard
    return redirect(url_for("dashboard"))

## dashboard page. Each page from here on should include each other and a 'log out'
@app.route("/dashboard")
def dashboard():
    return render_template("dashboard.html")

## budget page
@app.route("/budget")
def budget():
    return render_template("budget.html")

@app.route("/profile")
def profile():
    return render_template("profile.html")

@app.route("/setting")
def setting():
    return render_template("setting.html")

@app.route("/expenses")
def expenses():
    return render_template("expenses.html")


## For below, run the commands one at a time on the terminal. Except the last line, that is the link to where this app is running
## python -m venv venv
## venv\Scripts\activate  
## pip install flask
## python app.py
## http://127.0.0.1:5000
if __name__ == "__main__":
    app.run(debug=True)