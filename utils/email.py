from flask import url_for, current_app
from flask_mail import Message
import traceback

class EmailSender:
    def __init__(self, app):
        self.app = app
        self.mail = app.extensions.get('mail')
        if not self.mail:
            print("WARNING: Mail extension not found in app.extensions")
            print("Available extensions:", list(app.extensions.keys()))

    def send_email(self, recipient, subject, body, is_html=False):
        try:
            print(f"Attempting to send email to {recipient}")
            print(f"Mail configuration:")
            print(f"Server: {current_app.config['MAIL_SERVER']}")
            print(f"Port: {current_app.config['MAIL_PORT']}")
            print(f"Username: {current_app.config['MAIL_USERNAME']}")
            print(f"Use TLS: {current_app.config['MAIL_USE_TLS']}")
            
            if not self.mail:
                print("ERROR: Mail extension not initialized")
                return False

            msg = Message(
                subject=subject,
                recipients=[recipient],
                html=body if is_html else None,
                body=body if not is_html else None
            )
            
            with self.app.app_context():
                self.mail.send(msg)
            
            print("Email sent successfully")
            return True
        except Exception as e:
            print(f"Failed to send email: {str(e)}")
            print("Traceback:")
            traceback.print_exc()
            return False

    def send_verification_email(self, user):
        print(f"Sending verification email to {user.email}")
        verify_url = url_for('verify_email', token=user.verification_token, _external=True)
        subject = "Verify your email - Diatla Restaurant Admin"
        html_content = f"""
        <html>
            <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                    <h2 style="color: #2563eb;">Welcome to Diatla Restaurant Admin!</h2>
                    <p>Thank you for registering. Please verify your email address by clicking the button below:</p>
                    <div style="text-align: center; margin: 30px 0;">
                        <a href="{verify_url}" 
                           style="background-color: #2563eb; color: white; padding: 12px 24px; 
                                  text-decoration: none; border-radius: 5px; font-weight: bold;">
                            Verify Email
                        </a>
                    </div>
                    <p>If the button doesn't work, you can also copy and paste this link into your browser:</p>
                    <p style="word-break: break-all; color: #666;">{verify_url}</p>
                    <p>This link will expire in 24 hours.</p>
                    <hr style="border: none; border-top: 1px solid #eee; margin: 20px 0;">
                    <p style="color: #666; font-size: 12px;">
                        If you didn't create an account with us, please ignore this email.
                    </p>
                </div>
            </body>
        </html>
        """
        return self.send_email(user.email, subject, html_content, is_html=True)

    def send_reset_password_email(self, user):
        reset_url = url_for('reset_password', token=user.reset_token, _external=True)
        subject = "Reset your password - Diatla Restaurant Admin"
        html_content = f"""
        <html>
            <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                    <h2 style="color: #2563eb;">Reset Your Password</h2>
                    <p>We received a request to reset your password. Click the button below to create a new password:</p>
                    <div style="text-align: center; margin: 30px 0;">
                        <a href="{reset_url}" 
                           style="background-color: #2563eb; color: white; padding: 12px 24px; 
                                  text-decoration: none; border-radius: 5px; font-weight: bold;">
                            Reset Password
                        </a>
                    </div>
                    <p>If the button doesn't work, you can also copy and paste this link into your browser:</p>
                    <p style="word-break: break-all; color: #666;">{reset_url}</p>
                    <p>This link will expire in 1 hour.</p>
                    <hr style="border: none; border-top: 1px solid #eee; margin: 20px 0;">
                    <p style="color: #666; font-size: 12px;">
                        If you didn't request a password reset, please ignore this email or contact support if you're concerned.
                    </p>
                </div>
            </body>
        </html>
        """
        return self.send_email(user.email, subject, html_content, is_html=True)
