from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
import logging
import logging.handlers
import time
import uuid
import base64
import requests
import json
from typing import Optional, List
import urllib3
import os

# Disable SSL warnings when bypassing verification
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Import Version 2 Token Builder (generates 007 prefix tokens)
# Using build_token_with_rtm2 for unified RTC+RTM tokens
from app.token_builders import RtcTokenBuilder, Role_Publisher

from app.db.session import get_db
from app.models.user import User
from app.core.security import get_current_active_user
from app.core.config import settings
from app.services.vector_store_service import vector_store_service
from app.services.prompt_service import prompt_service
from pydantic import BaseModel

router = APIRouter()
logger = logging.getLogger(__name__)

# Configure file logging for detailed debugging
file_handler = logging.handlers.RotatingFileHandler(
    'backend.log',
    maxBytes=10*1024*1024,  # 10MB
    backupCount=5
)
file_handler.setLevel(logging.DEBUG)
file_formatter = logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
file_handler.setFormatter(file_formatter)
logger.addHandler(file_handler)
logger.setLevel(logging.DEBUG)


# Pydantic schemas
class GenerateTokenRequest(BaseModel):
    channel: Optional[str] = None
    uid: Optional[int] = 0


class GenerateTokenResponse(BaseModel):
    token: str  # RTC token for audio/video
    rtm_token: str  # RTM token for messaging/transcripts
    uid: int
    channel: str
    app_id: str


class InviteAgentRequest(BaseModel):
    requester_id: int
    channel_name: str
    video_id: Optional[int] = None  # Video ID to retrieve knowledge base context
    input_modalities: Optional[List[str]] = ["audio"]
    output_modalities: Optional[List[str]] = ["text", "audio"]
    tts_vendor: Optional[str] = "microsoft"  # "microsoft" or "elevenlabs"
    voice_name: Optional[str] = None  # Voice name/ID for the selected vendor


class InviteAgentResponse(BaseModel):
    agent_id: str
    channel: str
    status: str


class StopConversationRequest(BaseModel):
    agent_id: str


@router.get("/generate-token", response_model=GenerateTokenResponse)
async def generate_agora_token(
    channel: Optional[str] = None,
    uid: Optional[int] = 0,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """
    Generate Agora RTC token for voice communication.

    Args:
        channel: Channel name (auto-generated if not provided)
        uid: User ID (DEPRECATED - will be auto-generated)

    Returns:
        Token, UID, channel name, and app ID
    """
    try:
        # Validate Agora configuration
        if not settings.AGORA_APP_ID or not settings.AGORA_APP_CERTIFICATE:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Agora credentials not configured"
            )

        # Generate channel name if not provided
        if not channel:
            channel = f"voice_chat_{current_user.id}_{uuid.uuid4().hex[:8]}"

        # Generate a shorter random integer UID (6 digits) to avoid RTM "too long" error
        # RTM has stricter user ID length requirements than RTC
        import random
        generated_uid = random.randint(100000, 999999)

        # Token expiration time (1 hour = 3600 seconds)
        token_expire = 3600
        privilege_expire = 3600

        # Generate unified RTC+RTM token using build_token_with_rtm2
        # This single token works for both RTC (audio/video) and RTM (messaging/transcripts)
        rtm_uid_str = str(generated_uid)
        unified_token = RtcTokenBuilder.build_token_with_rtm2(
            app_id=settings.AGORA_APP_ID,
            app_certificate=settings.AGORA_APP_CERTIFICATE,
            channel_name=channel,
            rtc_account=generated_uid,  # RTC account (can be int or string)
            rtc_role=Role_Publisher,
            rtc_token_expire=token_expire,
            join_channel_privilege_expire=privilege_expire,
            pub_audio_privilege_expire=privilege_expire,
            pub_video_privilege_expire=privilege_expire,
            pub_data_stream_privilege_expire=privilege_expire,
            rtm_user_id=rtm_uid_str,  # RTM uses string user ID
            rtm_token_expire=token_expire
        )

        logger.info(f"Generated unified Agora RTC+RTM token (v2) for user {current_user.id}, channel: {channel}")
        logger.info(f"RTC UID (integer): {generated_uid}, RTM UID (string): '{rtm_uid_str}'")
        logger.info(f"Unified Token prefix: {unified_token[:3]}")

        return GenerateTokenResponse(
            token=unified_token,  # Use unified token for RTC
            rtm_token=unified_token,  # Same unified token works for RTM
            uid=generated_uid,
            channel=channel,
            app_id=settings.AGORA_APP_ID
        )

    except Exception as e:
        logger.error(f"Error generating Agora token: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate Agora token: {str(e)}"
        )


@router.post("/invite-agent", response_model=InviteAgentResponse)
async def invite_agent(
    request: InviteAgentRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """
    Invite AI agent to join voice conversation channel.

    Args:
        request: Channel and modality configuration

    Returns:
        Agent ID and status
    """
    try:
        # Validate Agora configuration
        if not settings.AGORA_APP_ID or not settings.AGORA_CUSTOMER_ID or not settings.AGORA_CUSTOMER_SECRET:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Agora Conversational AI credentials not configured"
            )

        # Generate unified token for agent using build_token_with_rtm2
        # Agent gets both RTC and RTM capabilities in a single token
        agent_uid = 999  # Fixed UID for agent
        token_expire = 3600  # 1 hour
        privilege_expire = 3600
        agent_uid_str = str(agent_uid)

        agent_token = RtcTokenBuilder.build_token_with_rtm2(
            app_id=settings.AGORA_APP_ID,
            app_certificate=settings.AGORA_APP_CERTIFICATE,
            channel_name=request.channel_name,
            rtc_account=agent_uid,  # RTC account
            rtc_role=Role_Publisher,
            rtc_token_expire=token_expire,
            join_channel_privilege_expire=privilege_expire,
            pub_audio_privilege_expire=privilege_expire,
            pub_video_privilege_expire=privilege_expire,
            pub_data_stream_privilege_expire=privilege_expire,
            rtm_user_id=agent_uid_str,  # RTM user ID (string)
            rtm_token_expire=token_expire
        )

        # Generate unique agent name
        unique_name = f"agent_{uuid.uuid4().hex[:8]}"

        # Retrieve video knowledge base context if video_id is provided
        knowledge_context = ""
        if request.video_id:
            try:
                logger.info(f"Retrieving knowledge base for video {request.video_id}")

                # Get all chunks from the video's vector store
                collection_info = vector_store_service.get_collection_info(request.video_id)

                if collection_info.get('exists') and collection_info.get('chunk_count', 0) > 0:
                    # Retrieve all transcript chunks (without query, get all)
                    # We'll do this by searching with a generic query to get comprehensive context
                    chunks = vector_store_service.search_similar_chunks(
                        video_id=request.video_id,
                        query="training content overview summary",
                        n_results=min(50, collection_info.get('chunk_count', 10))  # Get up to 50 chunks
                    )

                    if chunks:
                        # Build knowledge context from chunks
                        transcript_texts = []
                        for chunk in sorted(chunks, key=lambda x: x['metadata'].get('start_time', 0)):
                            start_time = chunk['metadata'].get('start_time', 0)
                            text = chunk['text']
                            transcript_texts.append(f"[{start_time:.1f}s] {text}")

                        knowledge_context = "\n".join(transcript_texts)
                        logger.info(f"Retrieved {len(chunks)} transcript chunks for video {request.video_id}")
                        logger.info(f"Knowledge context length: {len(knowledge_context)} characters")

                        # Limit knowledge context to prevent request size issues (max ~10000 chars)
                        MAX_KNOWLEDGE_CONTEXT_LENGTH = 10000
                        if len(knowledge_context) > MAX_KNOWLEDGE_CONTEXT_LENGTH:
                            logger.warning(f"Knowledge context too large ({len(knowledge_context)} chars), truncating to {MAX_KNOWLEDGE_CONTEXT_LENGTH} chars")
                            knowledge_context = knowledge_context[:MAX_KNOWLEDGE_CONTEXT_LENGTH] + "...\n\n[Note: Transcript truncated due to length. Ask me for specific details if needed.]"
                            logger.info(f"Truncated knowledge context length: {len(knowledge_context)} characters")
                else:
                    logger.warning(f"No knowledge base found for video {request.video_id}")
            except Exception as e:
                logger.error(f"Error retrieving knowledge base for video {request.video_id}: {e}")
                # Continue without knowledge context

        # Configure TTS (Text-to-Speech) based on vendor selection
        tts_vendor = request.tts_vendor.lower() if request.tts_vendor else "microsoft"

        if tts_vendor == "elevenlabs":
            # ElevenLabs TTS Configuration
            if not settings.ELEVENLABS_API_KEY:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="ElevenLabs API key not configured"
                )

            tts_config = {
                "vendor": "elevenlabs",
                "params": {
                    "key": settings.ELEVENLABS_API_KEY,
                    "voice_id": request.voice_name or settings.ELEVENLABS_VOICE_ID,
                    "model_id": settings.ELEVENLABS_MODEL_ID
                }
            }
            logger.info(f"Using ElevenLabs TTS with voice: {tts_config['params']['voice_id']}")
        else:
            # Microsoft Azure TTS Configuration (default)
            if not settings.MICROSOFT_TTS_KEY or not settings.MICROSOFT_TTS_REGION:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Microsoft Azure TTS credentials not configured"
                )

            tts_config = {
                "vendor": "microsoft",
                "params": {
                    "key": settings.MICROSOFT_TTS_KEY,
                    "region": settings.MICROSOFT_TTS_REGION,
                    "voice_name": request.voice_name or "en-US-AndrewMultilingualNeural"
                }
            }
            logger.info(f"Using Microsoft Azure TTS with voice: {tts_config['params']['voice_name']}")

        # Get base voice prompt from centralized service
        logger.info("Retrieving centralized prompt: voice_agent_base")
        base_prompt_config = prompt_service.render_prompt(
            db=db,
            prompt_name="voice_agent_base",
            variables={}
        )

        # Build system messages array
        system_messages = [
            {
                "role": "system",
                "content": base_prompt_config["system_message"]
            }
        ]

        # Add video knowledge context if available
        if knowledge_context:
            logger.info("Retrieving centralized prompt: voice_agent_knowledge")
            knowledge_prompt_config = prompt_service.render_prompt(
                db=db,
                prompt_name="voice_agent_knowledge",
                variables={"knowledge_context": knowledge_context}
            )
            system_messages.append({
                "role": "system",
                "content": knowledge_prompt_config["system_message"]
            })

        # Prepare agent invitation request
        request_body = {
            "name": unique_name,
            "properties": {
                "channel": request.channel_name,
                "token": agent_token,
                "agent_rtc_uid": str(agent_uid),
                "remote_rtc_uids": ["*"],  # Subscribe to all users
                "idle_timeout": 600,  # 10 minutes idle timeout (default is 30 seconds)
                "asr": {
                    "language": "en-US"
                },
                "llm": {
                    "url": "https://api.openai.com/v1/chat/completions",
                    "api_key": settings.OPENAI_API_KEY,
                    "system_messages": system_messages,
                    "params": {
                        "model": base_prompt_config["model"],
                        "max_tokens": base_prompt_config["max_tokens"],
                        "temperature": base_prompt_config["temperature"],
                        "top_p": base_prompt_config.get("top_p", 0.9)
                    }
                },
                "tts": tts_config,
                "advanced_features": {
                    "enable_rtm": True  # Enable RTM for transcript delivery
                },
                "parameters": {
                    "data_channel": "rtm",  # Use RTM as data channel for transcripts
                    "enable_metrics": True,
                    "enable_error_messages": True
                }
            }
        }

        # Make request to Agora Conversational AI API
        base_url = settings.AGORA_CONVO_AI_BASE_URL
        url = f"{base_url}/{settings.AGORA_APP_ID}/join"

        # Create basic auth header
        credentials = f"{settings.AGORA_CUSTOMER_ID}:{settings.AGORA_CUSTOMER_SECRET}"
        auth_header = base64.b64encode(credentials.encode()).decode()

        headers = {
            "Authorization": f"Basic {auth_header}",
            "Content-Type": "application/json"
        }

        print("=" * 80)
        print(f"[AGORA] Inviting agent to channel: {request.channel_name}")
        print(f"[AGORA] Using AGORA_CONVO_AI_BASE_URL: {settings.AGORA_CONVO_AI_BASE_URL}")
        print(f"[AGORA] Full request URL: {url}")
        print(f"[AGORA] Request headers: {json.dumps(headers, indent=2)}")
        print(f"[AGORA] Request body: {json.dumps(request_body, indent=2)}")
        print("=" * 80)

        # Log to file with full details
        logger.info("="*100)
        logger.info(f"AGORA VOICE ASSISTANT START REQUEST")
        logger.info(f"Channel: {request.channel_name}")
        logger.info(f"Video ID: {request.video_id}")
        logger.info(f"Agora API URL: {url}")
        logger.info(f"Request Headers: {json.dumps(headers, indent=2)}")
        logger.info(f"FULL REQUEST BODY:")
        logger.info(json.dumps(request_body, indent=2))
        logger.info("="*100)

        logger.info(f"Inviting agent to channel: {request.channel_name}")
        logger.info(f"Using AGORA_CONVO_AI_BASE_URL: {settings.AGORA_CONVO_AI_BASE_URL}")
        logger.info(f"Full request URL: {url}")
        logger.info(f"Request headers: {json.dumps(headers, indent=2)}")
        logger.info(f"Request body: {json.dumps(request_body, indent=2)}")

        # Try with SSL verification disabled (can help with SSL issues)
        try:
            logger.info("Sending POST request to Agora API...")
            logger.info(f"Request body size: {len(json.dumps(request_body))} bytes")

            response = requests.post(url, json=request_body, headers=headers, timeout=30, verify=True)

            print("=" * 80)
            print(f"[AGORA] Response status code: {response.status_code}")
            print(f"[AGORA] Response headers: {json.dumps(dict(response.headers), indent=2)}")
            try:
                print(f"[AGORA] Response body (JSON): {json.dumps(response.json(), indent=2)}")
            except:
                print(f"[AGORA] Response body (text): {response.text}")
            print("=" * 80)

            logger.info(f"Response status code: {response.status_code}")
            logger.info(f"Response body: {response.text}")
            response.raise_for_status()
        except requests.exceptions.ConnectionError as conn_err:
            logger.error(f"Connection error occurred: {conn_err}")
            logger.error(f"This might be due to request size ({len(json.dumps(request_body))} bytes) or network issues")
            print(f"[AGORA] CONNECTION ERROR: {conn_err}")
            print(f"[AGORA] Request body size: {len(json.dumps(request_body))} bytes")

            # If the request is very large, try reducing the knowledge context
            if len(json.dumps(request_body)) > 50000:  # 50KB threshold
                logger.warning("Request is very large, trying with reduced knowledge context...")
                # Truncate knowledge context to first 5000 characters
                if len(system_messages) > 1:
                    original_content = system_messages[1]['content']
                    system_messages[1]['content'] = original_content[:5000] + "...\n\n[Note: Knowledge context truncated due to size limits]"
                    request_body['properties']['llm']['system_messages'] = system_messages
                    logger.info(f"Reduced request body size: {len(json.dumps(request_body))} bytes")

                    # Retry with reduced context
                    response = requests.post(url, json=request_body, headers=headers, timeout=30, verify=True)
                    logger.info(f"Retry response status code: {response.status_code}")
                    logger.info(f"Retry response body: {response.text}")
                    response.raise_for_status()
                else:
                    raise
            else:
                raise
        except requests.exceptions.SSLError as ssl_err:
            logger.warning(f"SSL error occurred, retrying without SSL verification: {ssl_err}")
            print(f"[AGORA] SSL error, retrying without verification: {ssl_err}")

            # Retry without SSL verification
            response = requests.post(url, json=request_body, headers=headers, timeout=30, verify=False)

            print("=" * 80)
            print(f"[AGORA] Response status code: {response.status_code}")
            print(f"[AGORA] Response headers: {json.dumps(dict(response.headers), indent=2)}")
            try:
                print(f"[AGORA] Response body (JSON): {json.dumps(response.json(), indent=2)}")
            except:
                print(f"[AGORA] Response body (text): {response.text}")
            print("=" * 80)

            logger.info(f"Response status code: {response.status_code}")
            logger.info(f"Response body: {response.text}")
            response.raise_for_status()
        except requests.exceptions.HTTPError as http_err:
            print("=" * 80)
            print(f"[AGORA] HTTP ERROR occurred: {http_err}")
            print(f"[AGORA] Response status: {response.status_code}")
            try:
                print(f"[AGORA] Error response body (JSON): {json.dumps(response.json(), indent=2)}")
            except:
                print(f"[AGORA] Error response body (text): {response.text}")
            print("=" * 80)

            logger.error(f"HTTP error occurred: {http_err}")
            logger.error(f"Response status: {response.status_code}")
            logger.error(f"Response body: {response.text}")
            raise

        response_data = response.json()
        agent_id = response_data.get("agent_id", unique_name)

        print("=" * 80)
        print(f"[AGORA] Agent invited successfully!")
        print(f"[AGORA] Agent ID from Agora API: {agent_id}")
        print(f"[AGORA] Response status: {response_data.get('status')}")
        print(f"[AGORA] Returning to frontend: agent_id={agent_id}, channel={request.channel_name}")
        print("=" * 80)

        # Log response to file
        logger.info("="*100)
        logger.info("AGORA VOICE ASSISTANT START RESPONSE")
        logger.info(f"Agent invited successfully!")
        logger.info(f"Agent ID: {agent_id}")
        logger.info(f"Full Response: {json.dumps(response_data, indent=2)}")
        logger.info(f"Channel: {request.channel_name}")
        logger.info("="*100)

        logger.info(f"Agent invited successfully: {agent_id}")

        response_to_return = InviteAgentResponse(
            agent_id=agent_id,
            channel=request.channel_name,
            status="invited"
        )

        print(f"[AGORA] Response object: {response_to_return}")

        return response_to_return

    except requests.exceptions.RequestException as e:
        logger.error(f"Error calling Agora API: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to invite agent: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Error inviting agent: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to invite agent: {str(e)}"
        )


@router.post("/stop-conversation")
async def stop_conversation(
    request: StopConversationRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """
    Stop an ongoing conversation with AI agent.

    Args:
        request: Agent ID to stop

    Returns:
        Status message
    """
    try:
        # Validate Agora configuration
        if not settings.AGORA_APP_ID or not settings.AGORA_CUSTOMER_ID or not settings.AGORA_CUSTOMER_SECRET:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Agora Conversational AI credentials not configured"
            )

        # Make request to stop agent
        base_url = settings.AGORA_CONVO_AI_BASE_URL
        url = f"{base_url}/{settings.AGORA_APP_ID}/agents/{request.agent_id}/leave"

        # Create basic auth header
        credentials = f"{settings.AGORA_CUSTOMER_ID}:{settings.AGORA_CUSTOMER_SECRET}"
        auth_header = base64.b64encode(credentials.encode()).decode()

        headers = {
            "Authorization": f"Basic {auth_header}",
            "Content-Type": "application/json"
        }

        print("=" * 80)
        print(f"[AGORA] Stopping agent: {request.agent_id}")
        print(f"[AGORA] Stop agent URL: {url}")
        print(f"[AGORA] Request headers: {json.dumps(headers, indent=2)}")
        print("=" * 80)

        logger.info(f"Stopping agent: {request.agent_id}")
        logger.info(f"Stop agent URL: {url}")

        response = requests.post(url, headers=headers, timeout=30)

        print("=" * 80)
        print(f"[AGORA] Stop response status code: {response.status_code}")
        try:
            response_json = response.json()
            print(f"[AGORA] Stop response body (JSON): {json.dumps(response_json, indent=2)}")
        except:
            response_json = None
            print(f"[AGORA] Stop response body (text): {response.text}")
        print("=" * 80)

        logger.info(f"Stop response status: {response.status_code}")
        logger.info(f"Stop response body: {response.text}")

        # 404 means agent already left or doesn't exist - this is OK
        if response.status_code == 404:
            logger.info(f"Agent {request.agent_id} not found (404) - likely already left the channel")
            print(f"[AGORA] Agent {request.agent_id} already left or doesn't exist - treating as success")
            return {"status": "stopped", "agent_id": request.agent_id, "note": "Agent was not found (already left)"}

        response.raise_for_status()

        logger.info(f"Agent stopped successfully: {request.agent_id}")

        return {"status": "stopped", "agent_id": request.agent_id}

    except requests.exceptions.RequestException as e:
        logger.error(f"Error calling Agora API to stop agent: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to stop conversation: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Error stopping conversation: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to stop conversation: {str(e)}"
        )
