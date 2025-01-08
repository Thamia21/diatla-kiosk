# Diatla Restaurant & Bar - Digital Kiosk System 🍽️

![Python](https://img.shields.io/badge/python-3.8+-blue.svg)
![Flask](https://img.shields.io/badge/flask-2.0+-green.svg)
![License](https://img.shields.io/badge/license-MIT-blue.svg)

A modern, user-friendly digital kiosk system for Diatla Restaurant & Bar that allows customers to browse the menu and place orders efficiently. Built with Flask and modern web technologies.

![Kiosk Demo](static/img/demo.gif)

## ✨ Features

- 🎯 Interactive menu browsing by category
- ⚡ Real-time order management
- 💰 Dynamic price calculation
- 📱 Responsive design for various screen sizes
- 📧 Automated email confirmation system
- 🔒 Secure payment processing with Stripe
- 📨 Professional order confirmation emails

## 🚀 Quick Start

### Prerequisites

- Python 3.8+
- pip package manager
- Stripe account for payments
- EmailJS account for notifications

### Installation

1. Clone the repository
   ```bash
   git clone https://github.com/Thamia21/diatla-kiosk.git
   cd diatla-kiosk
   ```

2. Install dependencies
   ```bash
   pip install -r requirements.txt
   ```

3. Set up environment variables
   ```bash
   STRIPE_SECRET_KEY=your_stripe_secret_key
   STRIPE_PUBLISHABLE_KEY=your_stripe_publishable_key
   ```

## 📧 Email Configuration

The system uses EmailJS for sending order confirmation emails:

1. Create an account at [EmailJS](https://www.emailjs.com/)
2. Set up an email service (e.g., Gmail)
3. Create an email template
4. Update the following in `templates/payment_success.html`:
   ```javascript
   emailjs.init("your_emailjs_public_key");
   service_id: 'your_service_id',
   template_id: 'your_template_id'
   ```

## 🏃‍♂️ Running the Application

1. Start the Flask server:
   ```bash
   python app.py
   ```

2. Open your web browser and visit:
   ```
   http://localhost:5000
   ```

## 🏗️ Project Structure

```
diatla-kiosk/
├── app.py              # Main Flask application
├── auth.py             # Authentication logic
├── models.py           # Database models
├── templates/          # HTML templates
│   ├── index.html     # Main kiosk interface
│   ├── admin/         # Admin panel templates
│   └── email/         # Email templates
├── static/            # Static assets
│   ├── css/          # Stylesheets
│   ├── js/           # JavaScript files
│   └── img/          # Images
└── utils/            # Utility functions
```

## 🛠️ Technology Stack

- **Backend**: Python/Flask
- **Frontend**: HTML5, CSS3, JavaScript
- **UI Framework**: Bootstrap 5
- **Payment**: Stripe
- **Email**: EmailJS
- **Database**: SQLite
- **Icons**: Bootstrap Icons

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 📞 Support

If you have any questions or need support, please email at [your-email@example.com]
