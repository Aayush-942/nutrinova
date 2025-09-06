import streamlit as st
import requests
import pandas as pd
import plotly.express as px
from openai import OpenAI

# =============================
# CONFIGURATION
# =============================
from dotenv import load_dotenv
import os

load_dotenv()
USDA_API_KEY = os.getenv("USDA_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

client = OpenAI(api_key=OPENAI_API_KEY)

# Sample MET dataset (you can replace with API later)
EXERCISE_MET = {
    "Running (6 mph)": 9.8,
    "Cycling (moderate)": 7.5,
    "Walking (brisk)": 3.8,
    "Swimming": 6.0,
    "Yoga": 2.5,
    "Weightlifting": 6.0,
}


# =============================
# FUNCTIONS
# =============================

def search_food_usda(query):
    """Search food using USDA API"""
    url = f"https://api.nal.usda.gov/fdc/v1/foods/search?query={query}&api_key={USDA_API_KEY}"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        if "foods" in data and len(data["foods"]) > 0:
            return data["foods"]
    return []


def get_ai_insight(prompt):
    """Get AI-powered nutrition/fitness insights using OpenAI"""
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a helpful nutrition and fitness assistant."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=500
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"AI API Error: {e}"


def plot_nutrition(nutrition_df):
    """Plot a bar chart for nutrition values"""
    fig = px.bar(
        nutrition_df.melt(id_vars="Food", var_name="Nutrient", value_name="Amount"),
        x="Nutrient", y="Amount", color="Food", barmode="group"
    )
    st.plotly_chart(fig)


def calculate_calories_burned(weight_kg, exercise, duration_min):
    """Calculate calories burned using MET formula"""
    if exercise not in EXERCISE_MET:
        return 0
    met = EXERCISE_MET[exercise]
    calories = met * 3.5 * weight_kg / 200 * duration_min
    return round(calories, 2)


# =============================
# STREAMLIT UI
# =============================

st.set_page_config(page_title="NutriNova", layout="wide")

# Dark Mode Toggle
dark_mode = st.sidebar.checkbox("🌙 Dark Mode", value=False)
if dark_mode:
    st.markdown(
        """
        <style>
        body { background-color: #121212; color: #e0e0e0; }
        .stApp { background-color: #121212; color: #e0e0e0; }
        </style>
        """,
        unsafe_allow_html=True,
    )

st.title("🥗 NutriNova")
st.subheader("Smarter Food & Fitness Insights")

# Tabs for Food, Exercise, and Meal Planner
tabs = st.tabs(["🍎 Food Insights", "🏋️ Exercise Tracker", "📅 Meal Planner"])

# =============================
# FOOD TAB
# =============================
with tabs[0]:
    food_query = st.text_input("Enter a food item:", "")
    if food_query:
        foods = search_food_usda(food_query)
        if foods:
            st.success(f"Found {len(foods)} results for **{food_query}**")
            food_choices = {f["description"]: f for f in foods}
            selected_food = st.selectbox("Select a food:", list(food_choices.keys()))

            if selected_food:
                food_data = food_choices[selected_food]
                nutrients = {n["nutrientName"]: n["value"] for n in food_data["foodNutrients"][:5]}

                st.write("### Nutrition Info")
                st.json(nutrients)

                # AI Insight
                user_prompt = f"Give me a quick analysis of {selected_food} with these nutrients: {nutrients}"
                ai_response = get_ai_insight(user_prompt)

                st.subheader("🤖 AI Insights")
                st.write(ai_response)

                # Plot
                df = pd.DataFrame([nutrients], index=[selected_food]).reset_index().rename(columns={"index": "Food"})
                plot_nutrition(df)
        else:
            st.error("No results found. Try another food name.")

# =============================
# EXERCISE TAB
# =============================
with tabs[1]:
    st.write("### Track Your Exercise")
    weight = st.number_input("Enter your weight (kg):", min_value=30, max_value=200, value=70)
    exercise = st.selectbox("Select exercise:", list(EXERCISE_MET.keys()))
    duration = st.number_input("Duration (minutes):", min_value=5, max_value=300, value=30)

    if st.button("Calculate Calories Burned"):
        burned = calculate_calories_burned(weight, exercise, duration)
        st.success(f"🔥 You burned approximately **{burned} calories** doing {exercise} for {duration} minutes.")

# =============================
# MEAL PLANNER TAB
# =============================
with tabs[2]:
    st.write("### AI-Powered Meal Planner")
    daily_calories = st.number_input("Target daily calories:", min_value=1200, max_value=4000, value=2000)
    diet_type = st.selectbox("Diet preference:", ["Balanced", "Vegetarian", "Vegan", "Keto", "High-Protein"])

    if st.button("Generate Meal Plan"):
        prompt = f"Create a {diet_type} meal plan for 1 day with around {daily_calories} calories. Show breakfast, lunch, dinner, and snacks."
        meal_plan = get_ai_insight(prompt)
        st.subheader("🍽️ Your AI Meal Plan")
        st.write(meal_plan)
