"""
OpenAI service for generating AI responses for auto detailing shop chatbots.
Handles chat completions, shop-specific context, and booking assistance.
"""

import logging
from openai import AsyncOpenAI
import json
from typing import List, Optional, Dict, Any
from datetime import datetime
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.models.shop import Shop
from app.models.service import Service
from app.models.chat import ChatSession, ChatMessage
from app.core.config import settings


logger = logging.getLogger(__name__)

# Configure OpenAI client
openai_client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)


class AIResponse(BaseModel):
    """Response object from OpenAI service"""
    message: str
    tokens_used: int
    model: str
    suggestions: List[str] = []
    booking_prompt: Optional[str] = None
    services_mentioned: List[str] = []


class OpenAIService:
    """Service for handling OpenAI chat completions"""
    
    def __init__(self, db: Session):
        self.db = db
        self.model = getattr(settings, 'OPENAI_MODEL', 'gpt-3.5-turbo')  # Use configured model or default
        self.max_tokens = 500  # Reasonable limit for chat responses
        
        if not settings.OPENAI_API_KEY:
            logger.warning("OpenAI API key not configured - chat functionality disabled")
    
    async def generate_response(
        self,
        shop: Shop,
        message: str,
        session: ChatSession
    ) -> AIResponse:
        """
        Generate AI response for a customer message.
        
        Args:
            shop: Shop object with business context
            message: Customer message
            session: Chat session for context
            
        Returns:
            AIResponse object with generated response and metadata
        """
        if not settings.OPENAI_API_KEY:
            return self._get_fallback_response()
        
        try:
            # Get conversation history
            conversation_history = await self._get_conversation_history(session)
            
            # Build system prompt with shop context
            system_prompt = await self._build_system_prompt(shop)
            
            # Build messages for OpenAI
            messages = [
                {"role": "system", "content": system_prompt}
            ]
            
            # Add conversation history
            messages.extend(conversation_history)
            
            # Add current message
            messages.append({"role": "user", "content": message})
            
            # Generate response using new OpenAI client
            response = await openai_client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_tokens=self.max_tokens,
                temperature=0.7,  # Balanced creativity
                presence_penalty=0.1,  # Slight penalty for repetition
                frequency_penalty=0.1
            )
            
            # Extract response data
            ai_message = response.choices[0].message.content
            tokens_used = response.usage.total_tokens
            
            # Analyze response for additional features
            suggestions = await self._generate_suggestions(shop, message, ai_message)
            booking_prompt = await self._generate_booking_prompt(message, ai_message)
            services_mentioned = await self._extract_services_mentioned(shop, ai_message)
            
            return AIResponse(
                message=ai_message,
                tokens_used=tokens_used,
                model=self.model,
                suggestions=suggestions,
                booking_prompt=booking_prompt,
                services_mentioned=services_mentioned
            )
            
        except Exception as e:
            logger.error(f"OpenAI API error: {e}")
            return self._get_fallback_response()
    
    async def _build_system_prompt(self, shop: Shop) -> str:
        """Build system prompt with shop-specific context"""
        
        # Get shop services
        services = self.db.query(Service).filter(Service.shop_id == shop.id).all()
        services_text = ""
        if services:
            services_list = []
            for service in services:
                service_info = f"- {service.name}: {service.description}"
                if service.price:
                    service_info += f" (${service.price})"
                if service.duration_minutes:
                    service_info += f" (~{service.duration_minutes} minutes)"
                services_list.append(service_info)
            services_text = "\\n".join(services_list)
        else:
            services_text = "- Full Service Wash & Wax\\n- Interior Detailing\\n- Paint Correction\\n- Ceramic Coating"
        
        # Build comprehensive system prompt
        system_prompt = f"""You are a helpful AI assistant for {shop.name}, an auto detailing shop located at {shop.address}. 

BUSINESS INFORMATION:
- Shop Name: {shop.name}
- Location: {shop.address}
- Phone: {shop.phone}
- Greeting: {shop.greeting_message}

SERVICES OFFERED:
{services_text}

INSTRUCTIONS:
1. You are knowledgeable about auto detailing services, techniques, and best practices
2. Always be helpful, professional, and friendly
3. Focus on the customer's needs and recommend appropriate services
4. If asked about booking, pricing, or specific appointments, guide them to contact the shop directly
5. Stay focused on auto detailing topics - if asked about unrelated topics, politely redirect
6. Use the shop's services in your recommendations when relevant
7. Keep responses concise but informative (under 200 words typically)
8. If you don't know specific details about pricing or availability, suggest they call the shop

TONE AND STYLE:
- Professional yet approachable
- Enthusiastic about auto detailing
- Helpful and solution-oriented
- Use the shop's greeting style as a guide

Remember: You represent {shop.name} and should always maintain their professional image while being genuinely helpful to customers."""

        return system_prompt
    
    async def _get_conversation_history(self, session: ChatSession, limit: int = 10) -> List[Dict[str, str]]:
        """Get recent conversation history for context"""
        
        messages = self.db.query(ChatMessage).filter(
            ChatMessage.session_id == session.id
        ).order_by(ChatMessage.created_at.desc()).limit(limit * 2).all()
        
        # Reverse to get chronological order
        messages.reverse()
        
        conversation = []
        for msg in messages:
            role = "user" if msg.is_from_customer else "assistant"
            conversation.append({
                "role": role,
                "content": msg.message
            })
        
        return conversation
    
    async def _generate_suggestions(self, shop: Shop, user_message: str, ai_response: str) -> List[str]:
        """Generate follow-up suggestions based on the conversation"""
        
        suggestions = []
        user_lower = user_message.lower()
        
        # Service-based suggestions
        if any(word in user_lower for word in ["wash", "clean", "dirty"]):
            suggestions.extend([
                "What type of vehicle do you have?",
                "When was your last detail?",
                "Any specific problem areas?"
            ])
        
        elif any(word in user_lower for word in ["price", "cost", "how much"]):
            suggestions.extend([
                "What services are you interested in?",
                "What size is your vehicle?",
                "Would you like a package deal?"
            ])
        
        elif any(word in user_lower for word in ["book", "appointment", "schedule"]):
            suggestions.extend([
                "What day works best?",
                "Morning or afternoon preference?",
                "How soon do you need it done?"
            ])
        
        elif any(word in user_lower for word in ["ceramic", "coating", "protection"]):
            suggestions.extend([
                "What's your budget range?",
                "How long do you keep your car?",
                "Any previous coating experience?"
            ])
        
        # Default suggestions
        if not suggestions:
            suggestions = [
                "Tell me about your vehicle",
                "What's your main concern?",
                "Would you like to know about our packages?"
            ]
        
        return suggestions[:3]  # Limit to 3 suggestions
    
    async def _generate_booking_prompt(self, user_message: str, ai_response: str) -> Optional[str]:
        """Generate booking prompt if user seems ready to book"""
        
        user_lower = user_message.lower()
        booking_keywords = [
            "book", "appointment", "schedule", "when", "available",
            "today", "tomorrow", "this week", "next week",
            "ready", "let's do it", "sounds good", "interested"
        ]
        
        if any(keyword in user_lower for keyword in booking_keywords):
            return "Ready to book? Call us or let us know your preferred time!"
        
        return None
    
    async def _extract_services_mentioned(self, shop: Shop, ai_response: str) -> List[str]:
        """Extract services mentioned in the AI response"""
        
        services = self.db.query(Service).filter(Service.shop_id == shop.id).all()
        mentioned_services = []
        
        response_lower = ai_response.lower()
        
        for service in services:
            if service.name.lower() in response_lower:
                mentioned_services.append(service.name)
        
        # Also check for common service keywords
        service_keywords = {
            "wash": "Car Wash",
            "wax": "Waxing",
            "detail": "Detailing",
            "ceramic": "Ceramic Coating",
            "interior": "Interior Cleaning",
            "exterior": "Exterior Cleaning",
            "polish": "Polishing"
        }
        
        for keyword, service_name in service_keywords.items():
            if keyword in response_lower and service_name not in mentioned_services:
                mentioned_services.append(service_name)
        
        return mentioned_services
    
    def _get_fallback_response(self) -> AIResponse:
        """Get fallback response when OpenAI is unavailable"""
        
        fallback_messages = [
            "Thanks for your message! I'm currently experiencing some technical difficulties, but I'd be happy to help you with your auto detailing needs. Please call us directly for immediate assistance.",
            "Hi there! While I sort out a technical issue, feel free to browse our services or give us a call to discuss your detailing needs.",
            "Thank you for reaching out! I'm having some connection issues right now, but our team is standing by to help with all your auto detailing questions."
        ]
        
        import random
        message = random.choice(fallback_messages)
        
        return AIResponse(
            message=message,
            tokens_used=0,
            model="fallback",
            suggestions=["Call us directly", "View our services", "Check our location"],
            booking_prompt="Call us to schedule your appointment!"
        )


# Factory function for dependency injection
def get_openai_service(db: Session) -> OpenAIService:
    """Factory function to create OpenAIService instance"""
    return OpenAIService(db)