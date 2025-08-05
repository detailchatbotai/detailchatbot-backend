"""
Email service for sending authentication and notification emails.
Supports both SMTP and SendGrid backends for production flexibility.
"""

import logging
from typing import Optional, Dict, Any
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import smtplib
import ssl

from app.core.config import settings


logger = logging.getLogger(__name__)


class EmailError(Exception):
    """Custom exception for email-related errors"""
    pass


class EmailService:
    """Service for sending various types of emails"""
    
    def __init__(self):
        self.smtp_configured = bool(
            settings.SMTP_HOST and 
            settings.SMTP_USERNAME and 
            settings.SMTP_PASSWORD
        )
        
        if not self.smtp_configured:
            logger.warning("SMTP not configured - email functionality disabled")
    
    async def send_verification_email(self, email: str, verification_link: str) -> bool:
        """
        Send email verification email to user.
        
        Args:
            email: Recipient email address
            verification_link: URL for email verification
            
        Returns:
            True if email was sent successfully
        """
        subject = "Verify your DetailChatbot.ai account"
        
        # HTML email template
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Verify Your Email</title>
            <style>
                body {{
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                    line-height: 1.6;
                    color: #333;
                    max-width: 600px;
                    margin: 0 auto;
                    padding: 20px;
                }}
                .header {{
                    text-align: center;
                    margin-bottom: 30px;
                }}
                .button {{
                    display: inline-block;
                    padding: 15px 30px;
                    background-color: #007bff;
                    color: white;
                    text-decoration: none;
                    border-radius: 5px;
                    font-weight: bold;
                    margin: 20px 0;
                }}
                .footer {{
                    margin-top: 30px;
                    font-size: 14px;
                    color: #666;
                    border-top: 1px solid #eee;
                    padding-top: 20px;
                }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>DetailChatbot.ai</h1>
                <h2>Verify Your Email Address</h2>
            </div>
            
            <p>Welcome to DetailChatbot.ai! To complete your account setup, please verify your email address by clicking the button below:</p>
            
            <div style="text-align: center;">
                <a href="{verification_link}" class="button">Verify Email Address</a>
            </div>
            
            <p>If you can't click the button, copy and paste this link into your browser:</p>
            <p style="word-break: break-all; background: #f5f5f5; padding: 10px; border-radius: 3px;">
                {verification_link}
            </p>
            
            <p>This verification link will expire in 24 hours for security reasons.</p>
            
            <div class="footer">
                <p>If you didn't create an account with DetailChatbot.ai, you can safely ignore this email.</p>
                <p>Need help? Contact us at support@detailchatbot.ai</p>
            </div>
        </body>
        </html>
        """
        
        # Plain text fallback
        text_content = f"""
        Welcome to DetailChatbot.ai!
        
        To complete your account setup, please verify your email address by visiting:
        {verification_link}
        
        This verification link will expire in 24 hours for security reasons.
        
        If you didn't create an account with DetailChatbot.ai, you can safely ignore this email.
        
        Need help? Contact us at support@detailchatbot.ai
        """
        
        return await self._send_email(
            to_email=email,
            subject=subject,
            html_content=html_content,
            text_content=text_content
        )
    
    async def send_magic_link_email(self, email: str, magic_link: str) -> bool:
        """
        Send magic link for passwordless authentication.
        
        Args:
            email: Recipient email address  
            magic_link: URL for magic link authentication
            
        Returns:
            True if email was sent successfully
        """
        subject = "Your DetailChatbot.ai sign-in link"
        
        # HTML email template
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Sign In to DetailChatbot.ai</title>
            <style>
                body {{
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                    line-height: 1.6;
                    color: #333;
                    max-width: 600px;
                    margin: 0 auto;
                    padding: 20px;
                }}
                .header {{
                    text-align: center;
                    margin-bottom: 30px;
                }}
                .button {{
                    display: inline-block;
                    padding: 15px 30px;
                    background-color: #28a745;
                    color: white;
                    text-decoration: none;
                    border-radius: 5px;
                    font-weight: bold;
                    margin: 20px 0;
                }}
                .footer {{
                    margin-top: 30px;
                    font-size: 14px;
                    color: #666;
                    border-top: 1px solid #eee;
                    padding-top: 20px;
                }}
                .warning {{
                    background: #fff3cd;
                    border: 1px solid #ffeaa7;
                    border-radius: 5px;
                    padding: 15px;
                    margin: 20px 0;
                }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>DetailChatbot.ai</h1>
                <h2>Sign in to your account</h2>
            </div>
            
            <p>Click the button below to securely sign in to your DetailChatbot.ai account:</p>
            
            <div style="text-align: center;">
                <a href="{magic_link}" class="button">Sign In</a>
            </div>
            
            <p>If you can't click the button, copy and paste this link into your browser:</p>
            <p style="word-break: break-all; background: #f5f5f5; padding: 10px; border-radius: 3px;">
                {magic_link}
            </p>
            
            <div class="warning">
                <strong>Security Notice:</strong> This sign-in link will expire in 15 minutes and can only be used once.
            </div>
            
            <div class="footer">
                <p>If you didn't request this sign-in link, you can safely ignore this email.</p>
                <p>Need help? Contact us at support@detailchatbot.ai</p>
            </div>
        </body>
        </html>
        """
        
        # Plain text fallback
        text_content = f"""
        Sign in to DetailChatbot.ai
        
        Click the link below to securely sign in to your account:
        {magic_link}
        
        This sign-in link will expire in 15 minutes and can only be used once.
        
        If you didn't request this sign-in link, you can safely ignore this email.
        
        Need help? Contact us at support@detailchatbot.ai
        """
        
        return await self._send_email(
            to_email=email,
            subject=subject,
            html_content=html_content,
            text_content=text_content
        )
    
    async def send_welcome_email(self, email: str, shop_name: str) -> bool:
        """
        Send welcome email after shop creation.
        
        Args:
            email: User email
            shop_name: Name of the created shop
            
        Returns:
            True if email was sent successfully
        """
        subject = f"Welcome to DetailChatbot.ai - {shop_name} is ready!"
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Welcome to DetailChatbot.ai</title>
            <style>
                body {{
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                    line-height: 1.6;
                    color: #333;
                    max-width: 600px;
                    margin: 0 auto;
                    padding: 20px;
                }}
                .header {{
                    text-align: center;
                    margin-bottom: 30px;
                    background: linear-gradient(135deg, #007bff, #28a745);
                    color: white;
                    padding: 30px;
                    border-radius: 10px;
                }}
                .feature {{
                    background: #f8f9fa;
                    padding: 20px;
                    margin: 15px 0;
                    border-radius: 5px;
                    border-left: 4px solid #007bff;
                }}
                .next-steps {{
                    background: #e3f2fd;
                    padding: 20px;
                    border-radius: 5px;
                    margin: 20px 0;
                }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>Welcome to DetailChatbot.ai!</h1>
                <h2>Your shop "{shop_name}" is ready</h2>
            </div>
            
            <p>Congratulations! You've successfully set up your AI-powered chatbot for {shop_name}. Your customers can now get instant answers about your services, pricing, and booking information.</p>
            
            <div class="feature">
                <h3>What your chatbot can do:</h3>
                <ul>
                    <li>Answer questions about your detailing services</li>
                    <li>Provide pricing information</li>
                    <li>Help customers book appointments</li>
                    <li>Handle common inquiries 24/7</li>
                </ul>
            </div>
            
            <div class="next-steps">
                <h3>Next Steps:</h3>
                <ol>
                    <li>Add your services and pricing in the dashboard</li>
                    <li>Customize your chatbot's branding and messages</li>
                    <li>Get your widget code to add to your website</li>
                    <li>Set up calendar integration for bookings</li>
                </ol>
            </div>
            
            <div style="text-align: center; margin: 30px 0;">
                <a href="{settings.frontend_url}/dashboard" style="display: inline-block; padding: 15px 30px; background-color: #007bff; color: white; text-decoration: none; border-radius: 5px; font-weight: bold;">
                    Go to Dashboard
                </a>
            </div>
            
            <p>Questions? We're here to help! Contact us at support@detailchatbot.ai or check out our documentation.</p>
            
            <div style="margin-top: 30px; font-size: 14px; color: #666; border-top: 1px solid #eee; padding-top: 20px;">
                <p>Happy detailing!</p>
                <p>The DetailChatbot.ai Team</p>
            </div>
        </body>
        </html>
        """
        
        text_content = f"""
        Welcome to DetailChatbot.ai!
        
        Congratulations! You've successfully set up your AI-powered chatbot for {shop_name}.
        
        What your chatbot can do:
        - Answer questions about your detailing services
        - Provide pricing information  
        - Help customers book appointments
        - Handle common inquiries 24/7
        
        Next Steps:
        1. Add your services and pricing in the dashboard
        2. Customize your chatbot's branding and messages
        3. Get your widget code to add to your website
        4. Set up calendar integration for bookings
        
        Visit your dashboard: {settings.frontend_url}/dashboard
        
        Questions? Contact us at support@detailchatbot.ai
        
        Happy detailing!
        The DetailChatbot.ai Team
        """
        
        return await self._send_email(
            to_email=email,
            subject=subject,
            html_content=html_content,
            text_content=text_content
        )
    
    async def _send_email(
        self,
        to_email: str,
        subject: str,
        html_content: str,
        text_content: str,
        from_email: Optional[str] = None
    ) -> bool:
        """
        Send email using SMTP.
        
        Args:
            to_email: Recipient email
            subject: Email subject
            html_content: HTML email content
            text_content: Plain text email content  
            from_email: Sender email (optional)
            
        Returns:
            True if email was sent successfully
        """
        if not self.smtp_configured:
            logger.warning(f"SMTP not configured - would send email to {to_email}")
            # In development, just log the email instead of failing
            logger.info(f"Email content: {text_content}")
            return True
        
        try:
            # Setup email - use verified sender email
            from_email = from_email or "detailchatbot.ai@gmail.com"
            
            # Create message
            message = MIMEMultipart("alternative")
            message["Subject"] = subject
            message["From"] = from_email
            message["To"] = to_email
            
            # Add both plain text and HTML parts
            text_part = MIMEText(text_content, "plain")
            html_part = MIMEText(html_content, "html")
            
            message.attach(text_part)
            message.attach(html_part)
            
            # Send email
            context = ssl.create_default_context()
            # For SendGrid, we may need to disable certificate verification in development
            if settings.is_development:
                context.check_hostname = False
                context.verify_mode = ssl.CERT_NONE
            
            with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
                server.set_debuglevel(1)  # Enable debug output
                if settings.SMTP_TLS:
                    server.starttls(context=context)
                
                server.login(settings.SMTP_USERNAME, settings.SMTP_PASSWORD)
                server.send_message(message)
            
            logger.info(f"Email sent successfully to {to_email}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send email to {to_email}: {e}")
            # In development, don't fail completely
            if settings.is_development:
                logger.warning("Email failed but continuing in development mode")
                return True
            raise EmailError(f"Failed to send email: {str(e)}")