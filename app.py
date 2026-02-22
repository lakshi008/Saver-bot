import os
import sqlite3
from flask import Flask, render_template, request, redirect, url_for
from twilio.twiml.messaging_response import MessagingResponse
import google.generativeai as genai

# --------------------
# OLD Gemini Config ✅
# --------------------

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

# --------------------

app = Flask(__name__)

# --------------------
# Database Helper
# --------------------

def query_db(query, args=(), one=False):
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    cursor.execute(query, args)

    rows = cursor.fetchall()
    conn.commit()
    conn.close()

    return (rows[0] if rows else None) if one else rows

# --------------------
# Dashboard
# --------------------

@app.route("/")
def dashboard():

    search_query = request.args.get("search", "")

    if search_query:
        reels = query_db(
            "SELECT * FROM reels WHERE category LIKE ?",
            (f"%{search_query}%",)
        )
    else:
        reels = query_db("SELECT * FROM reels")

    return render_template(
        "dashboard.html",
        reels=reels,
        search_query=search_query
    )

# --------------------
# Delete Reel
# --------------------

@app.route("/delete/<int:reel_id>")
def delete_reel(reel_id):

    query_db("DELETE FROM reels WHERE id = ?", (reel_id,))

    return redirect(url_for("dashboard"))

# --------------------
# WhatsApp Bot 🔥🔥🔥
# --------------------

@app.route("/whatsapp", methods=["POST"])
def whatsapp_bot():

    incoming_msg = request.values.get("Body", "").strip()
    lower_msg = incoming_msg.lower()

    resp = MessagingResponse()
    msg = resp.message()

    try:

        fitness_keywords = [
            "workout", "gym", "fitness", "exercise", "training",
            "cardio", "strength", "muscle", "fat", "body"
        ]

        food_keywords = [
            "recipe", "food", "cook", "meal", "kitchen",
            "dish", "pasta", "cake", "healthy", "ingredients"
        ]

        travel_keywords = [
            "travel", "trip", "vacation", "beach", "hotel",
            "flight", "destination", "tour", "adventure", "explore"
        ]

        fashion_keywords = [
            "fashion", "outfit", "style", "look", "clothing",
            "dress", "trend", "wear", "model", "aesthetic"
        ]

        design_keywords = [
            "design", "ui", "ux", "interface", "layout",
            "dashboard", "branding", "visual", "graphics", "animation"
        ]

        if any(word in lower_msg for word in fitness_keywords):
            title = "Fitness Reel"
            category = "Fitness"
            summary = "Fitness content saved"

        elif any(word in lower_msg for word in food_keywords):
            title = "Food Reel"
            category = "Food & Recipes"
            summary = "Food content saved"

        elif any(word in lower_msg for word in travel_keywords):
            title = "Travel Reel"
            category = "Travel"
            summary = "Travel content saved"

        elif any(word in lower_msg for word in fashion_keywords):
            title = "Fashion Reel"
            category = "Fashion"
            summary = "Fashion content saved"

        elif any(word in lower_msg for word in design_keywords):
            title = "Design Reel"
            category = "Design"
            summary = "Design content saved"

        else:

            prompt = f"""
Classify this reel link:

{incoming_msg}

Categories:
Food & Recipes
Fitness
Travel
Fashion
Design

Return ONLY:

Title | Category | Summary
"""

            response = genai.generate_text(
                model="models/text-bison-001",
                prompt=prompt,
                temperature=0.2
            )

            output = response.result.strip()

            title, category, summary = output.split("|")

    except:
        title = "New Reel"
        category = "Fitness"
        summary = "Saved from WhatsApp"

    # ✅ Save WITHOUT thumbnail

    query_db(
        """
        INSERT INTO reels (title, category, summary, link)
        VALUES (?, ?, ?, ?)
        """,
        (title.strip(), category.strip(), summary.strip(), incoming_msg)
    )

    msg.body(f"🔥 Reel saved under {category}")

    return str(resp)

# --------------------

if __name__ == "__main__":
    app.run(debug=True)