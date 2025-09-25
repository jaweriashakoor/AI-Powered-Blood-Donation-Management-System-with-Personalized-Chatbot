# AI-Powered-Blood-Donation-Management-System-with-Personalized-Chatbot
A Flask-based web application that manages blood donations, recipients, stock levels, and appointments. It also includes a chatbot that can answer stock-related queries.
##  Features

**User Authentication** – Signup/Login system with password hashing
**SQLite Database** – Stores users, donations, recipients, and appointments
**Chatbot Integration** – Linked to stock, answers unit availability or “out of stock”
**Flash Messages** – Success/error messages for actions
**Appointment Booking** – Registered users can schedule donation appointments
**Donation & Recipient Tracking** – Full history for each user
**Stock Interface** – Shows live stock updates based on donations and requests
**Admin Panel** – Adjust stock manually (admin only)

##  Project Structure

```
AI BDMS/
│
├── main.py                # Flask app (core logic)
├── chatbot.py              # Chatbot logic (stock-aware)
├── data.db                 # SQLite database (auto-created on first run)
│
├── templates/              # HTML templates
│   ├── index.html
│   ├── signup.html
│   ├── login.html
│   ├── dashboard.html
│   ├── history.html
│   ├── book_appointment.html
│   ├── profile.html
│   └── admin.html
│
├── static/                 # Static assets
│   ├── css/style.css
│   └── js/chat.js
│
├── venv/                   # Virtual environment (optional, local only)
└── README.md               # Project documentation
``
##  Functionality Overview
###  User System
* **Signup** with name, email, password, role (`donor` or `recipient`), blood type, phone.
* **Login** with email + password.
* **Profile management** – update name, phone, blood type.
* **Session-based authentication** with Flask sessions.
###  Donations & Recipients
* Donors can log donations (`blood type`, `quantity`, `location`).
* Recipients can request blood.
* System checks **live stock availability** before confirming requests.
* Donations and requests are tracked in **history logs**.
## Appointments
* Users can book an appointment for donation.
* Stored in `appointments` table.
* Shown in **Dashboard**.
###  Chatbot
* Users can ask chatbot about blood availability.
* Example:
  * “How many units of O+ do you have?” → *“Currently 35 units available.”*
  * “Do you have AB-?” → *“Out of stock.”*
* Chatbot is enriched with user context if logged in.
###  Admin Panel
* Admin users (`is_admin=1`) can log in and adjust stock manually.
* Adjustments recorded in `donations` table for transparency.
* Admin can view stock summaries.
###  Stock Management
* **Base Stock** defined in `main.py`.
* Computed stock = **base stock + donations – recipients**.
* Always visible in templates (live updates).
# Database Schema
**Users Table**
* id, name, email, password, role, blood_type, phone, is_admin
**Donations Table**
* id, user_id, blood_type, quantity, location, donated_at
**Recipients Table**
* id, user_id, blood_type, quantity, location, received_at
**Appointments Table**
* id, user_id, scheduled_at, created
## Future Improvements
* Email/SMS reminders for appointments
* Role-based dashboards (donor vs recipient)
* AI-enhanced chatbot with natural language support
* REST API for mobile integration
# Tech Stack

* **Backend:** Python, Flask
* **Frontend:** HTML, CSS, JavaScript (Jinja2 templates)
* **Database:** SQLite
* **Authentication:** Werkzeug password hashing
* **Bot:** Simple Python chatbot with stock integration

Would you like me to also create a **`requirements.txt`** so you can install everything in one command (`pip install -r requirements.txt`)?
