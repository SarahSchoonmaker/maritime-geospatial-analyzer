#!/bin/bash

echo "📦 Running main.py to load vessel data..."
python main.py

echo "🚀 Launching Streamlit app..."
streamlit run app.py
