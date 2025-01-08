# Diatla Restaurant & Bar - Digital Kiosk System

A modern, user-friendly digital kiosk system for Diatla Restaurant & Bar that allows customers to browse the menu and place orders efficiently.

## Features

- Interactive menu browsing by category
- Real-time order management
- Dynamic price calculation
- Responsive design for various screen sizes
- Automated email confirmation system
- Secure payment processing with Stripe
- Professional order confirmation emails

## Installation

1. Make sure you have Python 3.8+ installed
2. Install the required dependencies:
   ```
   pip install -r requirements.txt
   ```
3. Set up environment variables:
   ```
   STRIPE_SECRET_KEY=your_stripe_secret_key
   STRIPE_PUBLISHABLE_KEY=your_stripe_publishable_key
   ```

## Email Configuration

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

## Running the Application

1. Navigate to the project directory:
   ```
   cd diatla-kiosk
   ```

2. Start the Flask server:
   ```
   python app.py
   ```

3. Open your web browser and visit:
   ```
   http://localhost:5000
   ```

## Project Structure

- `app.py` - Main Flask application and backend logic
- `templates/` - HTML templates
  - `index.html` - Main kiosk interface
- `static/` - Static assets
  - `css/style.css` - Custom styling
  - `js/main.js` - Frontend functionality
  - `img/` - Menu item images

## Technology Stack

- Backend: Python/Flask
- Frontend: HTML5, CSS3, JavaScript
- UI Framework: Bootstrap 5
- Payment Processing: Stripe
- Email Service: EmailJS
- Database: SQLite
- Icons: Bootstrap Icons
