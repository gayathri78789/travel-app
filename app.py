import streamlit as st
import os
import time
import requests
import folium

from groq import Groq
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderUnavailable, GeocoderTimedOut
from streamlit.components.v1 import html

# ---------------- PAGE CONFIG ----------------
st.set_page_config(
    page_title="AI Travel Planner for Students",
    page_icon="🧳",
    layout="wide"
)

# ---------------- TITLE ----------------
st.title("🧳 AI Travel Planner for Students")
st.write("AI-powered, budget-friendly travel planning for students 🎓")
st.divider()

# ---------------- USER INPUTS ----------------
st.header("📌 Enter Trip Details")

col1, col2 = st.columns(2)

with col1:
    source = st.text_input("Source City", placeholder="e.g., Hyderabad")

with col2:
    destination = st.text_input("Destination City", placeholder="e.g., Goa")

budget = st.slider("💰 Budget (in INR)", 1000, 20000, 5000, step=500)
days = st.number_input("📅 Number of Days", min_value=1, max_value=10, value=3)

interests = st.multiselect(
    "🎯 Select Your Interests",
    ["Food", "Beaches", "Temples", "Nature", "Museums", "Shopping"]
)

# ---------------- GROQ CLIENT ----------------
client = Groq(api_key=st.secrets["GROQ_API_KEY"])

# ---------- GEOCODING FUNCTION (SAFE) ----------
def get_coordinates(city):
    try:
        geolocator = Nominatim(
            user_agent="ai_travel_planner",
            timeout=10
        )
        time.sleep(1)  # avoid rate limit
        location = geolocator.geocode(city)
        if location:
            return location.latitude, location.longitude
    except (GeocoderUnavailable, GeocoderTimedOut):
        return None, None
    return None, None


# ---------- ROUTE FUNCTION ----------
def get_route(src_coords, dest_coords):
    try:
        url = (
            f"http://router.project-osrm.org/route/v1/driving/"
            f"{src_coords[1]},{src_coords[0]};"
            f"{dest_coords[1]},{dest_coords[0]}"
            f"?overview=full&geometries=geojson"
        )

        response = requests.get(url, timeout=10)
        data = response.json()

        if "routes" in data:
            return data["routes"][0]["geometry"]["coordinates"]
    except Exception:
        return []

    return []


# ---------- MAP DISPLAY FUNCTION ----------
def show_map(src_coords, dest_coords, route_coords):
    m = folium.Map(location=src_coords, zoom_start=6)

    folium.Marker(
        src_coords,
        tooltip="Source",
        icon=folium.Icon(color="green")
    ).add_to(m)

    folium.Marker(
        dest_coords,
        tooltip="Destination",
        icon=folium.Icon(color="red")
    ).add_to(m)

    if route_coords:
        route_latlon = [(lat, lon) for lon, lat in route_coords]
        folium.PolyLine(route_latlon, weight=5).add_to(m)

    return m


# ---------- BUDGET BREAKDOWN ----------
def calculate_budget(budget):
    return {
        "Transport": int(budget * 0.40),
        "Stay": int(budget * 0.35),
        "Food": int(budget * 0.20),
        "Misc": int(budget * 0.05),
    }


# ---------------- BUTTON ACTION ----------------
if st.button("✨ Generate AI Travel Plan"):

    if not source or not destination:
        st.warning("Please enter both source and destination")
    else:
        with st.spinner("AI is creating your travel plan... 🤖"):

            prompt = f"""
Create a budget-friendly travel itinerary for students.

Source: {source}
Destination: {destination}
Budget: ₹{budget}
Duration: {days} days
Interests: {', '.join(interests)}

Generate:
- Day-wise plan
- Affordable travel tips
- Budget food suggestions
- Low-cost stay ideas
"""

            response = client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=[
                    {"role": "system", "content": "You are a helpful travel planning assistant."},
                    {"role": "user", "content": prompt}
                ]
            )

            plan = response.choices[0].message.content

        # ---------------- OUTPUT ----------------
        st.success("✅ AI Travel Plan Generated")
        st.subheader("🧠 Your Personalized AI Travel Plan")
        st.write(plan)

        # ---------------- MAP OUTPUT ----------------
        st.subheader("🗺️ Travel Route Map")

        src_coords = get_coordinates(source)
        dest_coords = get_coordinates(destination)

        if all(src_coords) and all(dest_coords):
            try:
                route_coords = get_route(src_coords, dest_coords)
                travel_map = show_map(src_coords, dest_coords, route_coords)
                html(travel_map._repr_html_(), height=500)
            except Exception:
                st.warning("Map service temporarily unavailable.")
        else:
            st.warning("Unable to fetch map coordinates at the moment.")

        # ---------------- BUDGET BREAKDOWN ----------------
        st.subheader("💰 Estimated Budget Breakdown")

        breakdown = calculate_budget(budget)

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("🚗 Transport", f"₹{breakdown['Transport']}")
        c2.metric("🏨 Stay", f"₹{breakdown['Stay']}")
        c3.metric("🍽️ Food", f"₹{breakdown['Food']}")
        c4.metric("🧾 Misc", f"₹{breakdown['Misc']}")
