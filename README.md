# My Recipe Book Project 🍳

This is my "Recipe Book" website, built from scratch! It started as a simple page and has now grown into a full, feature-rich application.

It's powered by Python (using the Flask framework) and uses an SQLite database to store everything.

## ✨ What It Can Do

* **User System:** You can register, log in, and log out. Everyone can fill out their profile (first name, last name).
* **Dual Language:** The entire site (buttons, recipes, instructions) is fully translated between **Ukrainian (UK)** and **English (EN)**.
* **Reviews:** Users can leave reviews for recipes and even upload photos of their own creations.
* **Calculator:** On the "Calculator" tab, you can pick a recipe, set the number of portions, and the site will auto-calculate the new ingredient amounts. It also shows the estimated **Macros (Protein, Fat, Carbs)** for your serving.
* **"Potato Buddy":** A small animated mascot who pops up in the corner to comment on your actions (like greeting you or reacting to the calculator).
* **Interface:**
    * A black top-navigation bar using the `Arial Black` font.
    * All other text on the site uses `Times New Roman`.
    * All recipe titles are automatically set to `UPPERCASE`.
    * A **single click** on "Profile" opens an overlay panel. A **double click** opens the full "Edit Profile" page.
    * Toast notifications with food facts pop up every 3 minutes.

## 🛠️ What It's Built With (Tech Stack)

* **Backend:** Python (Flask)
* **Database:** SQLite (with Flask-SQLAlchemy)
* **Auth:** Flask-Login, Flask-Bcrypt
* **Frontend:** HTML, CSS (Grid, Flexbox), Vanilla JavaScript

## 🚀 How to Run This Project

### 1. Install the Libraries
You need to install the required Python packages. Open your terminal in the project folder and run:

```bash
pip install Flask Flask-SQLAlchemy Flask-Bcrypt Flask-Login
