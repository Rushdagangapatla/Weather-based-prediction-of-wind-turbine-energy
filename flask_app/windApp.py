from flask import Flask, render_template, request, session
import joblib
import requests
import os
from dotenv import load_dotenv
import webbrowser

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.secret_key = "windenergysecret"   # Required for session

# Load ML model
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
model_path = os.path.join(BASE_DIR, "power_prediction.pkl")
model = joblib.load(model_path)

# Weather API key
API_KEY = os.getenv("OPENWEATHER_API_KEY")


@app.route('/')
def home():
    return render_template("intro.html")


@app.route('/predict')
def predict():
    return render_template("predict.html",
                           temp=session.get('temp'),
                           humid=session.get('humid'),
                           pressure=session.get('pressure'),
                           speed=session.get('speed'),
                           prediction_text=session.get('prediction'),
                           input_theo=session.get('input_theo'),
                           input_wind=session.get('input_wind'),
                           city=session.get('city'))


# 🌦 WEATHER ROUTE
@app.route('/windapi', methods=['POST'])
def windapi():
    city = request.form.get('city')
    session['city'] = city   # Store selected city

    if not API_KEY:
        return render_template("predict.html", error="API key not configured")

    url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={API_KEY}&units=metric"

    try:
        resp = requests.get(url, timeout=5).json()

        if resp.get("cod") != 200:
            return render_template("predict.html", error=resp.get("message", "City not found"))

        session['temp'] = f"{resp['main']['temp']} °C"
        session['humid'] = f"{resp['main']['humidity']} %"
        session['pressure'] = f"{resp['main']['pressure']} hPa"
        session['speed'] = f"{resp['wind']['speed']} m/s"

        return render_template("predict.html",
                               temp=session['temp'],
                               humid=session['humid'],
                               pressure=session['pressure'],
                               speed=session['speed'],
                               prediction_text=session.get('prediction'),
                               input_theo=session.get('input_theo'),
                               input_wind=session.get('input_wind'),
                               city=session.get('city'))

    except Exception:
        return render_template("predict.html", error="Weather service unavailable")


# ⚡ PREDICTION ROUTE
@app.route('/y_predict', methods=['POST'])
def y_predict():
    try:
        theo = float(request.form['theo'])
        wind = float(request.form['wind'])

        session['input_theo'] = theo
        session['input_wind'] = wind

        prediction = model.predict([[wind, theo]])[0]
        session['prediction'] = f"Predicted Energy Output: {prediction:.2f} kW"

        return render_template("predict.html",
                               prediction_text=session['prediction'],
                               temp=session.get('temp'),
                               humid=session.get('humid'),
                               pressure=session.get('pressure'),
                               speed=session.get('speed'),
                               input_theo=session.get('input_theo'),
                               input_wind=session.get('input_wind'),
                               city=session.get('city'))

    except ValueError:
        return render_template("predict.html", error="Please enter valid numeric values.")



if __name__ == "__main__":
    if os.environ.get("WERKZEUG_RUN_MAIN") == "true":
        webbrowser.open_new("http://127.0.0.1:5000")
    app.run(host="127.0.0.1", port=5000, debug=True)

