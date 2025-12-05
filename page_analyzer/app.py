from flask import Flask, render_template
import os


app = Flask(__name__, template_folder="../templates")
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')


@app.get("/")
def home():
    return render_template("home.html")
