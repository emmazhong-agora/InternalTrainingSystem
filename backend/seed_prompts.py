#!/usr/bin/env python3
"""
Seed script to populate the database with existing AI prompts.

This script migrates the 7 hardcoded prompts from Chat and Voice AI services
into the centralized prompt_templates table.
"""

import sys
import os

# Add the backend directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.db.session import SessionLocal
from app.models.prompt import PromptTemplate
from app.models.material import VideoMaterial  # Import to resolve relationships


def seed_prompts():
    """Seed the database with existing prompts from Chat and Voice AI services."""

    db = SessionLocal()
    try:
        print("🌱 Seeding prompt templates...")
        print("=" * 80)

        # Check if prompts already exist
        existing_count = db.query(PromptTemplate).count()
        if existing_count > 0:
            print(f"⚠️  Found {existing_count} existing prompts.")
            response = input("Do you want to clear all existing prompts and reseed? (yes/no): ")
            if response.lower() == 'yes':
                db.query(PromptTemplate).delete()
                db.commit()
                print("✅ Cleared existing prompts.")
            else:
                print("❌ Seeding cancelled.")
                return

        prompts_to_create = [
            # CHAT SERVICE PROMPTS (5 total)

            # Prompt 1: Main Q&A System Prompt
            PromptTemplate(
                name="chat_qa_main",
                category="chat",
                description="Primary instruction set for answering user questions about video content",
                system_message="""You are an AI teaching assistant designed to help users understand video content they are watching.

Your role and guidelines:
1. When a user asks a question, use the provided transcript excerpts to reference specific content for explanation.
2. Provide detailed explanations and background information to help users better understand the video content.
3. Guide users to deeper learning by recommending additional resources and study suggestions when appropriate.
4. Adjust the difficulty and depth of your answers based on the user's learning progress to ensure the content is suitable for their comprehension level.
5. Maintain a friendly and encouraging tone to inspire users' interest in learning.

Important rules:
- Always reference the transcript timestamps when explaining specific video content.
- If the transcript doesn't contain information to answer the question, politely say so and offer to help with related topics that are covered.
- Be concise but thorough - aim for clear, helpful explanations.
- Encourage curiosity and deeper exploration of the subject matter.
- Use the transcript context provided to give accurate, relevant answers.""",
                user_message_template=None,  # User message built dynamically with RAG context
                model="gpt-4o",
                temperature=0.7,
                max_tokens=1000,
                top_p=1.0,
                variables=[],  # Static prompt, no variables
                response_format="text",
                version="1.0",
                is_active=True,
                is_default=True
            ),

            # Prompt 2: Context Engagement Prompt
            PromptTemplate(
                name="chat_context_engagement",
                category="chat",
                description="Generate engaging prompts based on current video playback position",
                system_message="You are an AI teaching assistant. Based on the video content the user is currently watching, generate a brief, engaging prompt (max 100 characters) to encourage them to ask questions or test their understanding. Be specific to the content.",
                user_message_template='Video content at {timestamp}s: "{current_content}"\n\nGenerate a prompt:',
                model="gpt-4o-mini",
                temperature=0.7,
                max_tokens=50,
                top_p=1.0,
                variables=["timestamp", "current_content"],
                response_format="text",
                version="1.0",
                is_active=True,
                is_default=True
            ),

            # Prompt 3: Quiz Generation Prompt
            PromptTemplate(
                name="quiz_generation",
                category="quiz",
                description="Generate multiple-choice quiz questions from video content",
                system_message="""You are a quiz generator for educational videos. Generate a {difficulty} difficulty multiple-choice question based on the provided video content.

Return your response in JSON format with these exact keys:
- question: the question text
- options: array of 4 option strings
- correct_answer: the index (0-3) of the correct option
- explanation: brief explanation of why the answer is correct

Make sure the question tests understanding, not just memorization.""",
                user_message_template="Video Content:\n{context_text}\n\nGenerate a quiz question:",
                model="gpt-4o",
                temperature=0.8,
                max_tokens=500,
                top_p=1.0,
                variables=["difficulty", "context_text"],
                response_format="json",
                response_schema={
                    "type": "object",
                    "properties": {
                        "question": {"type": "string"},
                        "options": {"type": "array", "items": {"type": "string"}, "minItems": 4, "maxItems": 4},
                        "correct_answer": {"type": "integer", "minimum": 0, "maximum": 3},
                        "explanation": {"type": "string"}
                    },
                    "required": ["question", "options", "correct_answer", "explanation"]
                },
                version="1.0",
                is_active=True,
                is_default=True
            ),

            # Prompt 4: Session Title Generation
            PromptTemplate(
                name="chat_session_title",
                category="chat",
                description="Generate concise titles for chat sessions based on first question",
                system_message="Generate a concise, descriptive title (max 50 characters) for a chat conversation based on the first question. Return only the title, no quotes or extra text.",
                user_message_template="First question: {first_question}\n\nGenerate a title:",
                model="gpt-4o-mini",
                temperature=0.5,
                max_tokens=20,
                top_p=1.0,
                variables=["first_question"],
                response_format="text",
                version="1.0",
                is_active=True,
                is_default=True
            ),

            # Prompt 5: Video Content Analysis
            PromptTemplate(
                name="video_content_analysis",
                category="analysis",
                description="Analyze video transcript to generate summary, outline, and key terms",
                system_message="""You are an expert content analyst for training videos. Analyze the video transcript and provide:

1. Summary: A concise 2-3 sentence overview of the main topics and takeaways
2. Outline: A structured outline of key sections (return as JSON array of objects with 'timestamp' and 'topic')
3. Key Terms: Important technical terms and concepts covered (return as JSON array of strings)

Return your response in valid JSON format with these exact keys: "summary", "outline", "key_terms".""",
                user_message_template="Analyze this video transcript:\n\n{transcript_text}",
                model="gpt-4o",
                temperature=0.5,
                max_tokens=1500,
                top_p=1.0,
                variables=["transcript_text"],
                response_format="json",
                response_schema={
                    "type": "object",
                    "properties": {
                        "summary": {"type": "string"},
                        "outline": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "timestamp": {"type": "string"},
                                    "topic": {"type": "string"}
                                },
                                "required": ["timestamp", "topic"]
                            }
                        },
                        "key_terms": {"type": "array", "items": {"type": "string"}}
                    },
                    "required": ["summary", "outline", "key_terms"]
                },
                version="1.0",
                is_active=True,
                is_default=True
            ),

            # VOICE AI SERVICE PROMPTS (2 total)

            # Prompt 6: Base Voice Agent System Prompt
            PromptTemplate(
                name="voice_agent_base",
                category="voice_ai",
                description="Base system instructions for voice AI teaching assistant",
                system_message="You are a helpful AI teaching assistant for an internal training system. You help learners understand video content, answer questions, and provide guidance. Keep your responses concise and clear for voice communication.",
                user_message_template=None,
                model="gpt-4o-mini",
                temperature=0.7,
                max_tokens=512,
                top_p=0.9,
                variables=[],  # Static prompt
                response_format="text",
                version="1.0",
                is_active=True,
                is_default=True
            ),

            # Prompt 7: Voice Agent Knowledge Context
            PromptTemplate(
                name="voice_agent_knowledge",
                category="voice_ai",
                description="Provide video transcript context to voice AI agent",
                system_message="Here is the complete transcript of the training video that the user is watching. Use this information to answer questions about the video content:\n\n{knowledge_context}",
                user_message_template=None,
                model="gpt-4o-mini",
                temperature=0.7,
                max_tokens=512,
                top_p=0.9,
                variables=["knowledge_context"],
                response_format="text",
                version="1.0",
                is_active=True,
                is_default=True
            ),
        ]

        # Create prompts
        for prompt in prompts_to_create:
            db.add(prompt)
            print(f"✅ Created: {prompt.name} ({prompt.category})")

        db.commit()

        print("=" * 80)
        print(f"🎉 Successfully seeded {len(prompts_to_create)} prompt templates!")
        print("\nPrompt Categories:")
        print("  - chat: 4 prompts")
        print("  - quiz: 1 prompt")
        print("  - voice_ai: 2 prompts")
        print("  - analysis: 1 prompt")
        print("\n✅ Database ready for unified prompt management!")

    except Exception as e:
        db.rollback()
        print(f"❌ Error seeding prompts: {e}")
        raise
    finally:
        db.close()


if __name__ == '__main__':
    seed_prompts()
