"""
Widget service for generating embeddable chatbot widgets.
Handles JavaScript widget generation and customization logic.
"""

import logging
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session

from app.models.shop import Shop
from app.core.config import settings

logger = logging.getLogger(__name__)


class WidgetService:
    """Service for handling widget generation and customization"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def _escape_js_string(self, text: str) -> str:
        """Escape a string for safe inclusion in JavaScript code"""
        if not text:
            return ""
        
        # Escape JavaScript special characters
        return (text
                .replace('\\', '\\\\')  # Escape backslashes first
                .replace("'", "\\'")    # Escape single quotes
                .replace('"', '\\"')    # Escape double quotes
                .replace('\n', '\\n')   # Escape newlines
                .replace('\r', '\\r')   # Escape carriage returns
                .replace('\t', '\\t'))  # Escape tabs
    
    def generate_widget_javascript(
        self,
        shop: Shop,
        theme: str = "light",
        position: str = "bottom-right"
    ) -> str:
        """
        Generate customized JavaScript widget code for a shop.
        
        Args:
            shop: Shop object with customization settings
            theme: Widget theme ("light" or "dark")
            position: Widget position ("bottom-right" or "bottom-left")
            
        Returns:
            JavaScript code as string
        """
        
        # Get shop customization
        primary_color = shop.primary_color or "#007bff"
        secondary_color = shop.secondary_color or "#6c757d"
        
        # Use the correct API base URL for the current environment
        if settings.is_development:
            api_base_url = "https://detailchatbot-api-dev.onrender.com/api/v1"
        else:
            api_base_url = "https://detailchatbot-api.onrender.com/api/v1"
        
        # Escape strings for JavaScript safety
        shop_name = self._escape_js_string(shop.name)
        greeting_message = self._escape_js_string(
            shop.greeting_message or f"Welcome to {shop.name}! How can I help you today?"
        )
        
        # Generate optimized widget JavaScript
        widget_js = f"""
(function() {{
    'use strict';
    
    // DetailChatbot.ai Widget Configuration
    const CONFIG = {{
        SHOP_API_KEY: '{shop.public_api_key}',
        API_BASE_URL: '{api_base_url}',
        THEME: '{theme}',
        POSITION: '{position}',
        SHOP_NAME: '{shop_name}',
        PRIMARY_COLOR: '{primary_color}',
        SECONDARY_COLOR: '{secondary_color}',
        GREETING: '{greeting_message}'
    }};
    
    // Widget state
    let state = {{
        sessionId: null,
        isOpen: false,
        isLoading: false,
        messageCount: 0
    }};
    
    // Utility Functions
    function generateSessionId() {{
        return 'session_' + Math.random().toString(36).substr(2, 9) + Date.now().toString(36);
    }}
    
    function createElement(tag, className, innerHTML) {{
        const element = document.createElement(tag);
        if (className) element.className = className;
        if (innerHTML) element.innerHTML = innerHTML;
        return element;
    }}
    
    function debounce(func, wait) {{
        let timeout;
        return function executedFunction(...args) {{
            const later = () => {{
                clearTimeout(timeout);
                func(...args);
            }};
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        }};
    }}
    
    // Widget Creation
    function createWidgetStructure() {{
        const container = createElement('div', 'detailchatbot-widget');
        container.innerHTML = `
            <div id="detailchatbot-button" class="detailchatbot-button detailchatbot-${{CONFIG.POSITION}} detailchatbot-${{CONFIG.THEME}}">
                <svg width="24" height="24" viewBox="0 0 24 24" fill="white">
                    <path d="M20 2H4c-1.1 0-2 .9-2 2v18l4-4h14c1.1 0 2-.9 2-2V4c0-1.1-.9-2-2-2zm0 14H6l-2 2V4h16v12z"/>
                </svg>
                <span class="detailchatbot-button-text">Chat</span>
            </div>
            
            <div id="detailchatbot-popup" class="detailchatbot-popup detailchatbot-${{CONFIG.POSITION}} detailchatbot-${{CONFIG.THEME}}" style="display: none;">
                <div class="detailchatbot-header">
                    <div class="detailchatbot-header-info">
                        <h3 class="detailchatbot-title">${{CONFIG.SHOP_NAME}}</h3>
                        <span class="detailchatbot-subtitle">AI Assistant</span>
                    </div>
                    <button id="detailchatbot-close" class="detailchatbot-close" aria-label="Close chat">&times;</button>
                </div>
                
                <div id="detailchatbot-messages" class="detailchatbot-messages">
                    <div class="detailchatbot-message detailchatbot-bot">
                        <div class="detailchatbot-avatar">
                            <svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor">
                                <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm0 18c-4.41 0-8-3.59-8-8s3.59-8 8-8 8 3.59 8 8-3.59 8-8 8z"/>
                            </svg>
                        </div>
                        <div class="detailchatbot-message-content">${{CONFIG.GREETING}}</div>
                    </div>
                </div>
                
                <div id="detailchatbot-suggestions" class="detailchatbot-suggestions"></div>
                
                <div class="detailchatbot-input-area">
                    <div class="detailchatbot-input-container">
                        <input type="text" id="detailchatbot-input" placeholder="Type your message..." maxlength="500" />
                        <button id="detailchatbot-send" class="detailchatbot-send-btn" aria-label="Send message">
                            <svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor">
                                <path d="M2.01 21L23 12 2.01 3 2 10l15 2-15 2z"/>
                            </svg>
                        </button>
                    </div>
                </div>
            </div>
        `;
        
        document.body.appendChild(container);
    }}
    
    // Styles
    function injectStyles() {{
        if (document.getElementById('detailchatbot-styles')) return;
        
        const style = createElement('style');
        style.id = 'detailchatbot-styles';
        style.textContent = `
            .detailchatbot-widget * {{
                box-sizing: border-box;
                font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            }}
            
            .detailchatbot-button {{
                position: fixed;
                z-index: 9999;
                background: ${{CONFIG.PRIMARY_COLOR}};
                color: white;
                border: none;
                border-radius: 28px;
                padding: 12px 20px;
                cursor: pointer;
                display: flex;
                align-items: center;
                gap: 8px;
                font-size: 14px;
                font-weight: 600;
                box-shadow: 0 4px 16px rgba(0,0,0,0.12);
                transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
                user-select: none;
            }}
            
            .detailchatbot-button:hover {{
                transform: translateY(-2px) scale(1.02);
                box-shadow: 0 8px 24px rgba(0,0,0,0.16);
            }}
            
            .detailchatbot-button.detailchatbot-bottom-right {{
                bottom: 20px;
                right: 20px;
            }}
            
            .detailchatbot-button.detailchatbot-bottom-left {{
                bottom: 20px;
                left: 20px;
            }}
            
            .detailchatbot-button-text {{
                font-weight: 600;
            }}
            
            .detailchatbot-popup {{
                position: fixed;
                z-index: 10000;
                width: 380px;
                height: 580px;
                background: white;
                border-radius: 16px;
                box-shadow: 0 12px 48px rgba(0,0,0,0.15);
                display: flex;
                flex-direction: column;
                overflow: hidden;
                opacity: 0;
                transform: translateY(20px) scale(0.95);
                transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
            }}
            
            .detailchatbot-popup[style*="flex"] {{
                opacity: 1;
                transform: translateY(0) scale(1);
            }}
            
            .detailchatbot-popup.detailchatbot-bottom-right {{
                bottom: 90px;
                right: 20px;
            }}
            
            .detailchatbot-popup.detailchatbot-bottom-left {{
                bottom: 90px;
                left: 20px;
            }}
            
            .detailchatbot-header {{
                background: linear-gradient(135deg, ${{CONFIG.PRIMARY_COLOR}}, ${{CONFIG.PRIMARY_COLOR}}dd);
                color: white;
                padding: 20px;
                display: flex;
                justify-content: space-between;
                align-items: center;
            }}
            
            .detailchatbot-title {{
                margin: 0;
                font-size: 16px;
                font-weight: 700;
                line-height: 1.2;
            }}
            
            .detailchatbot-subtitle {{
                font-size: 12px;
                opacity: 0.9;
                font-weight: 500;
            }}
            
            .detailchatbot-close {{
                background: rgba(255,255,255,0.2);
                border: none;
                color: white;
                width: 32px;
                height: 32px;
                border-radius: 50%;
                cursor: pointer;
                display: flex;
                align-items: center;
                justify-content: center;
                font-size: 18px;
                font-weight: 300;
                transition: background-color 0.2s;
            }}
            
            .detailchatbot-close:hover {{
                background: rgba(255,255,255,0.3);
            }}
            
            .detailchatbot-messages {{
                flex: 1;
                padding: 20px;
                overflow-y: auto;
                scroll-behavior: smooth;
                display: flex;
                flex-direction: column;
                gap: 16px;
            }}
            
            .detailchatbot-messages::-webkit-scrollbar {{
                width: 4px;
            }}
            
            .detailchatbot-messages::-webkit-scrollbar-track {{
                background: #f1f3f4;
            }}
            
            .detailchatbot-messages::-webkit-scrollbar-thumb {{
                background: #d2d3d4;
                border-radius: 4px;
            }}
            
            .detailchatbot-message {{
                display: flex;
                gap: 12px;
                max-width: 85%;
            }}
            
            .detailchatbot-message.detailchatbot-user {{
                flex-direction: row-reverse;
                margin-left: auto;
            }}
            
            .detailchatbot-avatar {{
                width: 32px;
                height: 32px;
                border-radius: 50%;
                background: ${{CONFIG.PRIMARY_COLOR}};
                color: white;
                display: flex;
                align-items: center;
                justify-content: center;
                flex-shrink: 0;
            }}
            
            .detailchatbot-message.detailchatbot-user .detailchatbot-avatar {{
                background: ${{CONFIG.SECONDARY_COLOR}};
            }}
            
            .detailchatbot-message-content {{
                padding: 12px 16px;
                border-radius: 18px;
                font-size: 14px;
                line-height: 1.5;
                word-wrap: break-word;
            }}
            
            .detailchatbot-message.detailchatbot-bot .detailchatbot-message-content {{
                background: #f8f9fa;
                color: #333;
            }}
            
            .detailchatbot-message.detailchatbot-user .detailchatbot-message-content {{
                background: ${{CONFIG.PRIMARY_COLOR}};
                color: white;
            }}
            
            .detailchatbot-suggestions {{
                padding: 0 20px;
                display: flex;
                flex-wrap: wrap;
                gap: 8px;
                margin-bottom: 8px;
            }}
            
            .detailchatbot-suggestion {{
                background: #f8f9fa;
                border: 1px solid #e9ecef;
                border-radius: 20px;
                padding: 8px 14px;
                font-size: 13px;
                cursor: pointer;
                transition: all 0.2s;
                color: #495057;
                font-weight: 500;
            }}
            
            .detailchatbot-suggestion:hover {{
                background: ${{CONFIG.PRIMARY_COLOR}};
                color: white;
                border-color: ${{CONFIG.PRIMARY_COLOR}};
                transform: translateY(-1px);
            }}
            
            .detailchatbot-input-area {{
                border-top: 1px solid #e9ecef;
                padding: 20px;
            }}
            
            .detailchatbot-input-container {{
                display: flex;
                gap: 12px;
                align-items: center;
            }}
            
            .detailchatbot-input-container input {{
                flex: 1;
                padding: 12px 16px;
                border: 1px solid #e9ecef;
                border-radius: 24px;
                font-size: 14px;
                outline: none;
                transition: border-color 0.2s;
            }}
            
            .detailchatbot-input-container input:focus {{
                border-color: ${{CONFIG.PRIMARY_COLOR}};
            }}
            
            .detailchatbot-send-btn {{
                width: 40px;
                height: 40px;
                background: ${{CONFIG.PRIMARY_COLOR}};
                color: white;
                border: none;
                border-radius: 50%;
                cursor: pointer;
                display: flex;
                align-items: center;
                justify-content: center;
                transition: all 0.2s;
                flex-shrink: 0;
            }}
            
            .detailchatbot-send-btn:hover {{
                transform: scale(1.05);
                box-shadow: 0 4px 12px rgba(0,0,0,0.15);
            }}
            
            .detailchatbot-send-btn:disabled {{
                opacity: 0.5;
                cursor: not-allowed;
                transform: none;
            }}
            
            .detailchatbot-typing {{
                display: flex;
                align-items: center;
                gap: 8px;
                color: #6c757d;
                font-size: 14px;
            }}
            
            .detailchatbot-typing-dots {{
                display: flex;
                gap: 3px;
            }}
            
            .detailchatbot-typing-dots span {{
                width: 6px;
                height: 6px;
                background: #6c757d;
                border-radius: 50%;
                animation: detailchatbot-bounce 1.4s infinite;
            }}
            
            .detailchatbot-typing-dots span:nth-child(2) {{
                animation-delay: 0.2s;
            }}
            
            .detailchatbot-typing-dots span:nth-child(3) {{
                animation-delay: 0.4s;
            }}
            
            @keyframes detailchatbot-bounce {{
                0%, 60%, 100% {{ 
                    transform: translateY(0);
                    opacity: 0.4; 
                }}
                30% {{ 
                    transform: translateY(-10px);
                    opacity: 1; 
                }}
            }}
            
            @media (max-width: 480px) {{
                .detailchatbot-popup {{
                    width: calc(100vw - 20px);
                    height: calc(100vh - 40px);
                    max-height: 600px;
                    bottom: 90px !important;
                    left: 10px !important;
                    right: 10px !important;
                }}
                
                .detailchatbot-button {{
                    bottom: 10px !important;
                    right: 10px !important;
                }}
            }}
        `;
        
        document.head.appendChild(style);
    }}
    
    // API Communication
    async function sendMessage(message) {{
        if (!state.sessionId) {{
            state.sessionId = generateSessionId();
        }}
        
        try {{
            const response = await fetch(`${{CONFIG.API_BASE_URL}}/chat/${{CONFIG.SHOP_API_KEY}}`, {{
                method: 'POST',
                headers: {{
                    'Content-Type': 'application/json',
                }},
                body: JSON.stringify({{
                    message: message,
                    session_id: state.sessionId
                }})
            }});
            
            if (!response.ok) {{
                throw new Error(`HTTP ${{response.status}}`);
            }}
            
            const data = await response.json();
            if (data.session_id) {{
                state.sessionId = data.session_id;
            }}
            
            return data;
        }} catch (error) {{
            console.warn('DetailChatbot API Error:', error);
            return {{
                message: "I'm having trouble connecting right now. Please try again in a moment or contact us directly at {shop.phone}.",
                suggestions: ["Try again", "Call us directly"],
                session_id: state.sessionId
            }};
        }}
    }}
    
    // Message Management
    function addMessage(message, isUser = false, showAvatar = true) {{
        const messagesContainer = document.getElementById('detailchatbot-messages');
        const messageDiv = createElement('div', `detailchatbot-message detailchatbot-${{isUser ? 'user' : 'bot'}}`);
        
        messageDiv.innerHTML = `
            ${{showAvatar ? `<div class="detailchatbot-avatar">
                <svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor">
                    <path d="${{isUser ? 'M12 12c2.21 0 4-1.79 4-4s-1.79-4-4-4-4 1.79-4 4 1.79 4 4 4zm0 2c-2.67 0-8 1.34-8 4v2h16v-2c0-2.66-5.33-4-8-4z' : 'M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm0 18c-4.41 0-8-3.59-8-8s3.59-8 8-8 8 3.59 8 8-3.59 8-8 8z'}}"/>
                </svg>
            </div>` : ''}}
            <div class="detailchatbot-message-content">${{message}}</div>
        `;
        
        messagesContainer.appendChild(messageDiv);
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
        state.messageCount++;
    }}
    
    function showTyping() {{
        const messagesContainer = document.getElementById('detailchatbot-messages');
        const typingDiv = createElement('div', 'detailchatbot-message detailchatbot-bot');
        typingDiv.id = 'detailchatbot-typing-indicator';
        typingDiv.innerHTML = `
            <div class="detailchatbot-avatar">
                <svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor">
                    <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm0 18c-4.41 0-8-3.59-8-8s3.59-8 8-8 8 3.59 8 8-3.59 8-8 8z"/>
                </svg>
            </div>
            <div class="detailchatbot-typing">
                Typing
                <div class="detailchatbot-typing-dots">
                    <span></span>
                    <span></span>
                    <span></span>
                </div>
            </div>
        `;
        messagesContainer.appendChild(typingDiv);
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
    }}
    
    function hideTyping() {{
        const typingDiv = document.getElementById('detailchatbot-typing-indicator');
        if (typingDiv) typingDiv.remove();
    }}
    
    function showSuggestions(suggestions) {{
        const container = document.getElementById('detailchatbot-suggestions');
        container.innerHTML = '';
        
        suggestions.slice(0, 3).forEach(suggestion => {{
            const btn = createElement('div', 'detailchatbot-suggestion', suggestion);
            btn.onclick = () => {{
                document.getElementById('detailchatbot-input').value = suggestion;
                handleSendMessage();
            }};
            container.appendChild(btn);
        }});
    }}
    
    const handleSendMessage = debounce(async function() {{
        const input = document.getElementById('detailchatbot-input');
        const sendBtn = document.getElementById('detailchatbot-send');
        const message = input.value.trim();
        
        if (!message || state.isLoading) return;
        
        // Update UI
        state.isLoading = true;
        input.value = '';
        sendBtn.disabled = true;
        addMessage(message, true);
        showTyping();
        
        // Send message
        const response = await sendMessage(message);
        
        // Update UI with response
        hideTyping();
        addMessage(response.message);
        
        if (response.suggestions && response.suggestions.length > 0) {{
            showSuggestions(response.suggestions);
        }}
        
        // Reset state
        state.isLoading = false;
        sendBtn.disabled = false;
        input.focus();
    }}, 300);
    
    // Event Handlers
    function setupEventListeners() {{
        const button = document.getElementById('detailchatbot-button');
        const popup = document.getElementById('detailchatbot-popup');
        const closeBtn = document.getElementById('detailchatbot-close');
        const input = document.getElementById('detailchatbot-input');
        const sendBtn = document.getElementById('detailchatbot-send');
        
        button.onclick = () => {{
            popup.style.display = state.isOpen ? 'none' : 'flex';
            state.isOpen = !state.isOpen;
            if (state.isOpen) {{
                input.focus();
                // Show initial suggestions if no messages yet
                if (state.messageCount <= 1) {{
                    showSuggestions([
                        "What services do you offer?",
                        "How much does detailing cost?",
                        "Can I book an appointment?"
                    ]);
                }}
            }}
        }};
        
        closeBtn.onclick = () => {{
            popup.style.display = 'none';
            state.isOpen = false;
        }};
        
        input.onkeypress = (e) => {{
            if (e.key === 'Enter' && !e.shiftKey) {{
                e.preventDefault();
                handleSendMessage();
            }}
        }};
        
        sendBtn.onclick = handleSendMessage;
        
        // Close on outside click
        document.onclick = (e) => {{
            const isClickInsideWidget = e.target.closest('.detailchatbot-widget');
            if (!isClickInsideWidget && state.isOpen) {{
                popup.style.display = 'none';
                state.isOpen = false;
            }}
        }};
    }}
    
    // Initialize
    function init() {{
        // Prevent multiple initializations
        if (document.getElementById('detailchatbot-widget')) {{
            console.warn('DetailChatbot widget already initialized');
            return;
        }}
        
        injectStyles();
        createWidgetStructure();
        setupEventListeners();
        
        console.log('DetailChatbot widget initialized for {shop.name}');
    }}
    
    // Start when DOM is ready
    if (document.readyState === 'loading') {{
        document.addEventListener('DOMContentLoaded', init);
    }} else {{
        init();
    }}
}})();
"""
        
        return widget_js
    
    def get_widget_config(self, shop: Shop) -> Dict[str, Any]:
        """
        Get widget configuration for a shop.
        
        Args:
            shop: Shop object
            
        Returns:
            Dict with widget configuration
        """
        return {
            "shop_name": shop.name,
            "shop_api_key": shop.public_api_key,
            "primary_color": shop.primary_color or "#007bff",
            "secondary_color": shop.secondary_color or "#6c757d",
            "greeting_message": shop.greeting_message or f"Welcome to {shop.name}! How can I help you today?",
            "phone": shop.phone,
            "address": shop.address,
            "is_active": shop.is_active
        }

# Factory function for dependency injection
def get_widget_service(db: Session = None) -> WidgetService:
    """Factory function to create WidgetService instance"""
    # Note: db parameter is kept for compatibility but not used in widget service
    # Widget service doesn't need database operations for JavaScript generation
    return WidgetService(db)