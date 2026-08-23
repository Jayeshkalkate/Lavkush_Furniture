# 🪑 Lavkush Furniture – Full Stack E-Commerce Platform

Lavkush Furniture is a production-ready **Full Stack Furniture E-Commerce Web Application** built using **Python & Django**, designed to simulate a real-world online shopping system with secure authentication, product management, payments, analytics, and admin control.

🔗 **Live Website:** https://lavkushfurniture.onrender.com  
💻 **GitHub Repository:** https://github.com/Jayeshkalkate/Lavkush_Furniture  

---

# 📌 Project Overview

Lavkush Furniture is not just a product gallery — it is a complete e-commerce ecosystem that includes:

- User authentication system
- Product catalog with filtering
- Wishlist & Cart functionality
- Razorpay Payment Gateway integration
- Order management system
- Bulk product upload (CSV/Excel support)
- Admin analytics dashboard
- Cloud media hosting
- Secure deployment with DevOps practices

This project demonstrates real-world implementation of Django-based scalable web architecture.

---

# 🚀 Core Features

## 👤 Customer Features

- ✅ Secure User Registration & Login
- ✅ Profile Management
- ✅ Browse Furniture by Category
- ✅ Advanced Filtering (Price, Rating, Category)
- ✅ Product Detail Page with Specifications
- ✅ Wishlist ❤️ System
- ✅ Add to Cart 🛒
- ✅ Quantity Management
- ✅ Razorpay Secure Payment Gateway
- ✅ Order Confirmation & Receipt Generation (PDF)
- ✅ Order History
- ✅ Ratings & Reviews System
- ✅ Fully Responsive UI (Mobile + Desktop)
- ✅ SEO Friendly Structure

---

## 🔐 Admin (Superuser) Features

- 🔑 Django Admin Control Panel
- ➕ Add / Edit / Delete Products
- 📦 Bulk Upload Products via CSV/Excel
- 📊 Sales Analytics Dashboard
- 👥 Manage Users
- 📋 Order Monitoring
- ⭐ Manage Reviews
- 🖼 Manage Product Images via Cloudinary
- 🧾 Payment Tracking
- 📈 Revenue Summary

---

# 💳 Payment Integration

- Integrated with **Razorpay API**
- Secure transaction handling
- Payment verification
- Order creation only after successful payment
- Receipt generation system
- Protection against duplicate payments

---

# 📊 Analytics & Monitoring

- Total Revenue Calculation
- Total Orders Count
- Best Selling Products
- User Growth Monitoring
- Monthly Sales Overview
- Admin Dashboard Metrics

---

# 📦 Bulk Upload System

Admin can:
- Upload CSV/Excel sheet
- Automatically create multiple products
- Validate data before saving
- Handle image URLs dynamically
- Reduce manual data entry

---

# 🛠️ Technology Stack

| Layer        | Technologies Used |
|-------------|------------------|
| Frontend     | HTML5, CSS3, Bootstrap 5, JavaScript |
| Backend      | Python, Django |
| Database     | SQLite (Development), PostgreSQL (Production Ready) |
| Media Storage| Cloudinary |
| Payment      | Razorpay |
| Deployment   | Render |
| Version Control | Git & GitHub |
| DevOps Tools | Docker (Ready Setup), CI/CD Concepts |
| IDE          | VS Code |

---

# 🏗️ Project Architecture

```
Lavkush_Furniture/
│
├── account/           # Authentication System
├── gallery/           # Product Management
├── cart/              # Cart & Wishlist Logic
├── order/             # Payment & Order Handling
├── analytics/         # Revenue & Dashboard Metrics
├── templates/         # HTML Templates
├── static/            # CSS, JS, Assets
├── media/             # Uploaded Media
├── manage.py
└── requirements.txt
```

---

# 🔒 Security Implementations

- CSRF Protection
- Secure Payment Verification
- Login Required Decorators
- Admin-only Views Protection
- Session Management
- Data Validation before saving
- Atomic Database Transactions

---

# 🧪 Installation & Local Setup

```bash
# Clone Repository
git clone https://github.com/Jayeshkalkate/Lavkush_Furniture.git
cd Lavkush_Furniture

# Create Virtual Environment
python -m venv env
env\Scripts\activate   # Windows
# source env/bin/activate (Mac/Linux)

# Install Dependencies
pip install -r requirements.txt

# Apply Migrations
python manage.py migrate

# Create Superuser
python manage.py createsuperuser

# Run Server
python manage.py runserver
```

Visit: http://127.0.0.1:8000

---

# 🌍 Deployment

- Hosted on **Render**
- Connected with GitHub Auto Deploy
- Environment Variables for:
  - SECRET_KEY
  - DEBUG
  - DATABASE_URL
  - Razorpay Keys
  - Cloudinary Credentials

---

# 👨‍💻 Developer

**Jayesh Rajendra Kalkate**  
B.Tech Computer Engineering (2022–2026)  
Godavari College of Engineering, Jalgaon  

📧 kalkatejayesh@gmail.com  
📱 +91 84829 98343  
🌐 Portfolio: https://devjayesh-portfolio.netlify.app  
🔗 LinkedIn: https://www.linkedin.com/in/jayesh-kalkate-31a250242  
💻 GitHub: https://github.com/Jayeshkalkate  

---

# 📜 License

This project is licensed under the MIT License.

---

# 💡 Project Purpose

Lavkush Furniture was built to:

- Demonstrate Full Stack Django expertise
- Showcase real-world E-Commerce architecture
- Practice payment gateway integration
- Implement secure authentication systems
- Apply DevOps & deployment practices
- Build a portfolio-ready production-level project

---

> Built with passion, real-world architecture, and production mindset 🚀
