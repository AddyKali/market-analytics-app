# market-analytics-app
📊 Market Analytics App

A full-stack web application that provides real-time stock market analytics with a modern UI and live data streaming using WebSockets.

<img width="719" height="416" alt="image" src="https://github.com/user-attachments/assets/5f20b22f-255f-47c5-9a95-24aefa67f1f3" />



▶ Backend Setup (FastAPI)

Open a terminal inside the backend folder:
# Create virtual environment
python -m venv venv

# Activate on Windows
venv\Scripts\activate

# Install required packages
pip install -r requirements.txt

# Run FastAPI server
uvicorn app.main:app --reload
http://localhost:8000

http://localhost:8000



💻 Frontend Setup (React + Vite)

Open a terminal inside the frontend folder:

# Install dependencies
npm install

# Start development server
npm run dev


http://localhost:5173

🔌 API / WebSocket Integration

Make sure your frontend uses correct URLs:

// Example config
export const API_BASE_URL = "http://localhost:8000";
export const WS_URL = "ws://localhost:8000/ws";


✨ Features

✔ Real-time stock market data updates
✔ Interactive dashboards & visual charts
✔ WebSocket-powered live streaming
✔ Clean modular code structure
✔ Easy local setup and development

🛠 Future Improvements

Add user authentication

Support for multiple stock indices

Cloud deployment for global access

Alerts for price movements

Historical data charts & analysis

👨‍💻 Author

Adarsh Kumar — Full-Stack Developer
Building skills in modern web technologies 🚀
