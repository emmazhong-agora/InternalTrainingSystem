import React, { useState, useEffect, useRef } from 'react';
import AgoraRTC, {
  AgoraRTCProvider,
  useRTCClient,
  useJoin,
  useLocalMicrophoneTrack,
  usePublish,
  useRemoteUsers,
  useClientEvent,
} from 'agora-rtc-react';
import AgoraRTM from 'agora-rtm';
import { agoraAPI } from '../services/api';
import { DebugPanel } from './DebugPanel';
import { debugLogger } from '../utils/debugLogger';
import { ConversationalAIAPI } from '../conversational-ai-api';
import {
  EConversationalAIAPIEvents,
  ETranscriptHelperMode,
  ETurnStatus,
  type ITranscriptHelperItem,
  type IUserTranscription,
  type IAgentTranscription,
} from '../conversational-ai-api/type';

interface VoiceChatProps {
  videoId: number;
  currentTimestamp?: number;
  onClose?: () => void;
}

interface TranscriptMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
}

// Enable Agora SDK logging
AgoraRTC.enableLogUpload();
AgoraRTC.setLogLevel(0); // 0 = DEBUG, 1 = INFO, 2 = WARNING, 3 = ERROR, 4 = NONE

// CRITICAL: Enable audio PTS metadata BEFORE creating RTC client
// This is required for the Conversational AI API to receive transcripts
(AgoraRTC as any).setParameter("ENABLE_AUDIO_PTS_METADATA", true);
console.log('[AGORA SDK] ✅ Audio PTS metadata enabled for transcript delivery');

// Create Agora RTC client with auto-subscribe enabled
const agoraClient = AgoraRTC.createClient({
  mode: 'rtc',
  codec: 'vp8',
});

console.log('[AGORA SDK] Log upload enabled, log level set to DEBUG');

// Component to play remote user audio
const RemoteAudioPlayer: React.FC<{ user: any }> = ({ user }) => {
  const audioTrackRef = React.useRef<any>(null);
  const playAttemptRef = React.useRef<number>(0);

  useEffect(() => {
    console.log('='.repeat(80));
    console.log(`[RemoteAudioPlayer] Effect triggered for user ${user.uid}`);
    console.log(`[RemoteAudioPlayer] user.audioTrack:`, user.audioTrack);
    console.log(`[RemoteAudioPlayer] user.hasAudio:`, user.hasAudio);
    console.log(`[RemoteAudioPlayer] audioTrackRef.current:`, audioTrackRef.current);
    console.log('='.repeat(80));

    const playAudio = async () => {
      try {
        if (!user.audioTrack) {
          console.warn(`[RemoteAudioPlayer] No audio track available for user ${user.uid}`);
          return;
        }

        if (audioTrackRef.current === user.audioTrack) {
          console.log(`[RemoteAudioPlayer] Audio track already playing for user ${user.uid}`);
          return;
        }

        playAttemptRef.current += 1;
        const attemptNumber = playAttemptRef.current;

        console.log(`[RemoteAudioPlayer] Attempt #${attemptNumber}: Playing audio from user ${user.uid}`);
        console.log(`[RemoteAudioPlayer] Audio track object:`, user.audioTrack);
        console.log(`[RemoteAudioPlayer] Audio track type:`, user.audioTrack.constructor.name);
        console.log(`[RemoteAudioPlayer] Audio track isPlaying:`, user.audioTrack.isPlaying);
        console.log(`[RemoteAudioPlayer] Audio track enabled:`, user.audioTrack.enabled);
        console.log(`[RemoteAudioPlayer] Audio track muted:`, user.audioTrack.muted);
        console.log(`[RemoteAudioPlayer] Audio track volume:`, user.audioTrack.getVolumeLevel?.());

        audioTrackRef.current = user.audioTrack;

        console.log(`[RemoteAudioPlayer] Calling audioTrack.play()...`);
        const playResult = await user.audioTrack.play();
        console.log(`[RemoteAudioPlayer] ✅ audioTrack.play() completed successfully for user ${user.uid}`);
        console.log(`[RemoteAudioPlayer] Play result:`, playResult);
        console.log(`[RemoteAudioPlayer] After play - isPlaying:`, user.audioTrack.isPlaying);

      } catch (error) {
        console.error(`[RemoteAudioPlayer] ❌ Error playing audio from user ${user.uid}:`, error);
        console.error(`[RemoteAudioPlayer] Error details:`, {
          message: (error as Error).message,
          name: (error as Error).name,
          stack: (error as Error).stack,
        });

        // Detect autoplay blocking
        if ((error as Error).name === 'NotAllowedError' ||
            (error as Error).message?.includes('autoplay') ||
            (error as Error).message?.includes('user interaction')) {
          console.warn('[RemoteAudioPlayer] 🚫 Browser blocked autoplay - user interaction required');
        }
      }
    };

    playAudio();

    return () => {
      if (audioTrackRef.current) {
        try {
          console.log(`[RemoteAudioPlayer] Cleanup: Stopping audio from user ${user.uid}`);
          audioTrackRef.current.stop();
          audioTrackRef.current = null;
        } catch (error) {
          console.error(`[RemoteAudioPlayer] Error stopping audio:`, error);
        }
      }
    };
  }, [user.audioTrack, user.uid, user.hasAudio]);

  return null;
};

const VoiceChatInner: React.FC<VoiceChatProps> = ({ videoId, currentTimestamp, onClose }) => {
  const client = useRTCClient();
  const [isConnecting, setIsConnecting] = useState(false);
  const [isConnected, setIsConnected] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [agentId, setAgentId] = useState<string | null>(null);
  const [channelInfo, setChannelInfo] = useState<{
    token: string;  // RTC token for audio/video
    rtm_token: string;  // RTM token for messaging/transcripts
    uid: number;
    channel: string;
    app_id: string;
  } | null>(null);

  // Microphone control
  const [micEnabled, setMicEnabled] = useState(true);
  const { localMicrophoneTrack } = useLocalMicrophoneTrack(micEnabled);

  // TTS configuration
  const [ttsVendor, setTtsVendor] = useState<'microsoft' | 'elevenlabs'>('microsoft');
  const [voiceName, setVoiceName] = useState<string>('');

  // Remote users (AI agent)
  const remoteUsers = useRemoteUsers();

  // Transcript display (real-time only, not stored)
  const [transcriptMessages, setTranscriptMessages] = useState<TranscriptMessage[]>([]);
  const transcriptEndRef = useRef<HTMLDivElement>(null);
  const [audioBlocked, setAudioBlocked] = useState(false);

  // RTM client and Conversational AI API for receiving transcripts
  const rtmClientRef = useRef<any>(null);
  const conversationalAIAPIRef = useRef<any>(null);

  // Debug panel
  const [showDebug, setShowDebug] = useState(false);

  // Auto-scroll to latest transcript message
  const scrollTranscriptToBottom = () => {
    transcriptEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollTranscriptToBottom();
  }, [transcriptMessages]);

  // Add transcript message helper
  const addTranscriptMessage = (role: 'user' | 'assistant', content: string) => {
    const newMessage: TranscriptMessage = {
      id: `${Date.now()}-${Math.random()}`,
      role,
      content,
      timestamp: new Date(),
    };
    setTranscriptMessages((prev) => [...prev, newMessage]);
  };

  // Clear transcript
  const handleClearTranscript = () => {
    setTranscriptMessages([]);
  };

  // Real-time transcript integration using Agora Conversational AI API
  // The Agora Conversational AI API handles all RTM messaging and transcript delivery.
  // Implementation:
  // - Initialize ConversationalAIAPI with RTC and RTM instances
  // - Subscribe to TRANSCRIPT_UPDATED events
  // - API automatically handles RTM messages, parsing, and aggregation
  // - Provides word-by-word rendering with status tracking
  // - No manual RTM message handling required
  //
  // Event types:
  // - TRANSCRIPT_UPDATED: Complete transcript history with user and assistant messages
  // - AGENT_STATE_CHANGED: Agent state transitions (idle, listening, thinking, speaking)
  // - AGENT_ERROR: Error events from agent modules
  //
  // See: Conversational AI API initialization effect below for implementation

  // Join channel when we have credentials
  const joinResult = useJoin(
    {
      appid: channelInfo?.app_id || '',
      channel: channelInfo?.channel || '',
      token: channelInfo?.token || '',
      uid: channelInfo?.uid || 0,
    },
    channelInfo !== null,
  );

  // Log join status and enable volume indicator
  useEffect(() => {
    if (channelInfo) {
      console.log('[AGORA JOIN] Attempting to join channel:', {
        appid: channelInfo.app_id,
        channel: channelInfo.channel,
        uid: channelInfo.uid,
      });

      // Enable volume indicator to monitor audio levels
      client.enableAudioVolumeIndicator();
      console.log('[AGORA JOIN] Audio volume indicator enabled');
    }
  }, [channelInfo, client]);

  // Publish local microphone track
  usePublish([localMicrophoneTrack]);

  // Listen for user joined event
  useClientEvent(client, 'user-joined', (user) => {
    console.log('User joined:', user.uid);
    setIsConnected(true);
  });

  // Listen for user left event
  useClientEvent(client, 'user-left', (user) => {
    console.log('User left:', user.uid);
    if (user.uid.toString() === '999') {
      // Agent left
      setIsConnected(false);
    }
  });

  // Initialize Conversational AI API for transcript delivery via RTM
  useEffect(() => {
    if (!channelInfo) {
      console.log('[ConversationalAI] No channel info yet, skipping initialization');
      return;
    }

    console.log('[ConversationalAI] ===== Starting Conversational AI API Initialization =====');
    console.log('[ConversationalAI] Channel info:', channelInfo);

    const initializeConversationalAI = async () => {
      try {
        // Create RTM client with appId and userId
        const userId = String(channelInfo.uid);
        console.log('[ConversationalAI] Creating RTM client');
        console.log('[ConversationalAI] APP_ID:', channelInfo.app_id);
        console.log('[ConversationalAI] User ID:', userId);

        const rtmConfig = {
          logUpload: true,
          logLevel: 'debug' as const,
        };

        const rtmClient = new AgoraRTM.RTM(channelInfo.app_id, userId, rtmConfig);
        rtmClientRef.current = rtmClient;

        // Add event listeners for debugging
        rtmClient.addEventListener('status', (status: any) => {
          console.log('[RTM] Status change:', status);
        });

        console.log('[ConversationalAI] Logging into RTM...');
        await rtmClient.login({ token: channelInfo.rtm_token });
        console.log('[ConversationalAI] ✅ RTM logged in successfully');

        // Initialize Conversational AI API
        console.log('[ConversationalAI] Initializing Conversational AI API');
        const conversationalAIAPI = ConversationalAIAPI.init({
          rtcEngine: client,
          rtmEngine: rtmClient,
          renderMode: ETranscriptHelperMode.WORD, // Word-by-word rendering
        });
        conversationalAIAPIRef.current = conversationalAIAPI;

        // Subscribe to transcript updates
        console.log('[ConversationalAI] Subscribing to TRANSCRIPT_UPDATED events');
        conversationalAIAPI.on(
          EConversationalAIAPIEvents.TRANSCRIPT_UPDATED,
          (transcripts: ITranscriptHelperItem<Partial<IUserTranscription | IAgentTranscription>>[]) => {
            console.log('='.repeat(80));
            console.log('[ConversationalAI] ✉️  TRANSCRIPT_UPDATED event received');
            console.log('[ConversationalAI] Total transcripts:', transcripts.length);
            console.log('[ConversationalAI] User UID from channelInfo:', channelInfo.uid);
            console.log('='.repeat(80));

            // Convert transcripts to messages
            const messages: TranscriptMessage[] = transcripts.map((t) => {
              // Compare transcript UID with the user's actual UID from channelInfo
              // User UID is a random 6-digit number, agent UID is 999
              const role = Number(t.uid) === channelInfo.uid ? 'user' : 'assistant';

              // Add status indicator for in-progress messages
              let content = t.text;
              if (t.status === ETurnStatus.IN_PROGRESS) {
                content += ' [...]';
              } else if (t.status === ETurnStatus.INTERRUPTED) {
                content += ' [interrupted]';
              }

              console.log(`[Transcript] UID=${t.uid}, Role=${role}, Status=${t.status}, Text="${content}"`);

              return {
                id: `${t.turn_id}-${t.uid}-${t._time}`,
                role,
                content,
                timestamp: new Date(t._time),
              };
            });

            setTranscriptMessages(messages);
            console.log('[ConversationalAI] ✅ UI updated with', messages.length, 'messages');
          }
        );

        // Subscribe to agent state changes (optional, for debugging)
        conversationalAIAPI.on(
          EConversationalAIAPIEvents.AGENT_STATE_CHANGED,
          (agentUserId: string, event: any) => {
            console.log(`[ConversationalAI] Agent ${agentUserId} state changed to:`, event.state);
          }
        );

        // Subscribe to agent errors (optional, for debugging)
        conversationalAIAPI.on(
          EConversationalAIAPIEvents.AGENT_ERROR,
          (agentUserId: string, error: any) => {
            console.error(`[ConversationalAI] Agent ${agentUserId} error:`, error);
          }
        );

        // Subscribe to channel messages
        console.log(`[ConversationalAI] Subscribing to channel: "${channelInfo.channel}"`);
        conversationalAIAPI.subscribeMessage(channelInfo.channel);
        console.log('[ConversationalAI] ✅ Subscribed to channel messages');
        console.log('[ConversationalAI] ===== Conversational AI API Initialization Complete =====');
      } catch (error) {
        console.error('[ConversationalAI] ❌ Initialization error:', error);
        console.error('[ConversationalAI] Error details:', (error as Error).message);
        console.error('[ConversationalAI] Error stack:', (error as Error).stack);
      }
    };

    initializeConversationalAI();

    // Cleanup on unmount
    return () => {
      console.log('[ConversationalAI] ===== Cleaning up Conversational AI API =====');
      if (conversationalAIAPIRef.current) {
        console.log('[ConversationalAI] Unsubscribing and destroying API');
        try {
          conversationalAIAPIRef.current.unsubscribe();
          conversationalAIAPIRef.current.destroy();
        } catch (err) {
          console.error('[ConversationalAI] Cleanup error:', err);
        }
      }
      if (rtmClientRef.current) {
        console.log('[ConversationalAI] Logging out RTM client');
        try {
          rtmClientRef.current.logout().catch((err: any) =>
            console.error('[RTM] Logout error:', err)
          );
        } catch (err) {
          console.error('[RTM] Logout error:', err);
        }
      }
    };
  }, [channelInfo, client]);

  // Listen for user published (audio/video track)
  useClientEvent(client, 'user-published', async (user, mediaType) => {
    try {
      console.log('='.repeat(80));
      console.log('[AGORA EVENT] user-published event triggered');
      console.log('[AGORA EVENT] User UID:', user.uid);
      console.log('[AGORA EVENT] Media type:', mediaType);
      console.log('[AGORA EVENT] User object:', user);
      console.log('='.repeat(80));

      console.log('[AGORA EVENT] Subscribing to user:', user.uid, mediaType);
      await client.subscribe(user, mediaType);
      console.log('[AGORA EVENT] ✅ Successfully subscribed to:', user.uid, mediaType);

      // IMPORTANT: Play audio immediately after subscribing
      if (mediaType === 'audio') {
        console.log('[AGORA EVENT] Audio track subscribed, checking user.audioTrack...');
        console.log('[AGORA EVENT] user.audioTrack:', user.audioTrack);
        console.log('[AGORA EVENT] user.hasAudio:', user.hasAudio);

        if (user.audioTrack) {
          console.log('[AGORA EVENT] ✅ Audio track is available on user object');
          console.log('[AGORA EVENT] Audio track details:', {
            isPlaying: user.audioTrack.isPlaying,
            enabled: user.audioTrack.enabled,
            muted: user.audioTrack.muted,
          });

          // Play the audio track immediately
          console.log('[AGORA EVENT] Calling user.audioTrack.play()...');
          try {
            await user.audioTrack.play();
            console.log('[AGORA EVENT] ✅✅✅ Successfully called play() on audio track for user', user.uid);
            console.log('[AGORA EVENT] After play() - isPlaying:', user.audioTrack.isPlaying);
            setAudioBlocked(false); // Audio playing successfully
          } catch (playError) {
            console.error('[AGORA EVENT] ❌ Error calling play() on audio track:', playError);
            console.error('[AGORA EVENT] Error name:', (playError as Error).name);
            console.error('[AGORA EVENT] Error message:', (playError as Error).message);

            // Detect autoplay blocking
            if ((playError as Error).name === 'NotAllowedError' ||
                (playError as Error).message?.includes('autoplay') ||
                (playError as Error).message?.includes('user interaction')) {
              console.warn('[AGORA EVENT] 🚫 Browser blocked autoplay - user interaction required');
              setAudioBlocked(true);
            }
          }
        } else {
          console.warn('[AGORA EVENT] ⚠️ Audio track not found on user object after subscription');
        }
      }
    } catch (error) {
      console.error('[AGORA EVENT] ❌ Error subscribing to user:', user.uid, mediaType, error);
    }
  });

  // Listen for user unpublished
  useClientEvent(client, 'user-unpublished', (user, mediaType) => {
    console.log('[AGORA EVENT] User unpublished:', user.uid, 'mediaType:', mediaType);
  });

  // Listen for connection state changes
  useClientEvent(client, 'connection-state-change', (curState, prevState, reason) => {
    console.log('[AGORA EVENT] Connection state changed:', {
      previous: prevState,
      current: curState,
      reason: reason,
    });
  });

  // Listen for volume indicator
  useClientEvent(client, 'volume-indicator', (volumes) => {
    volumes.forEach((volume) => {
      if (volume.level > 0) {
        console.log(`[AGORA EVENT] Volume from user ${volume.uid}: ${volume.level}`);
      }
    });
  });

  // Monitor remote users
  useEffect(() => {
    console.log('='.repeat(80));
    console.log('[REMOTE USERS] Remote users list updated');
    console.log('[REMOTE USERS] Count:', remoteUsers.length);
    console.log('[REMOTE USERS] UIDs:', remoteUsers.map(u => u.uid));

    remoteUsers.forEach(user => {
      console.log(`[REMOTE USERS] User ${user.uid}:`, {
        hasAudio: user.hasAudio,
        hasVideo: user.hasVideo,
        audioTrack: user.audioTrack ? 'present' : 'null',
        videoTrack: user.videoTrack ? 'present' : 'null',
      });

      if (user.audioTrack) {
        console.log(`[REMOTE USERS] User ${user.uid} audio track details:`, {
          isPlaying: user.audioTrack.isPlaying,
          enabled: user.audioTrack.enabled,
          muted: user.audioTrack.muted,
          volume: user.audioTrack.getVolumeLevel?.(),
        });
      }
    });
    console.log('='.repeat(80));
  }, [remoteUsers]);

  // Start voice conversation
  const handleStartConversation = async () => {
    setIsConnecting(true);
    setError(null);

    try {
      // Step 1: Generate Agora token
      console.log('Generating Agora token...');
      const tokenResponse = await agoraAPI.generateToken();
      console.log('Token generated:', tokenResponse);

      setChannelInfo(tokenResponse);

      // Step 2: Invite AI agent to channel
      console.log('Inviting AI agent with TTS vendor:', ttsVendor);
      console.log('Video ID for knowledge base:', videoId);
      const agentResponse = await agoraAPI.inviteAgent({
        requester_id: tokenResponse.uid,
        channel_name: tokenResponse.channel,
        video_id: videoId,  // Pass video ID to retrieve knowledge base
        input_modalities: ['audio'],
        output_modalities: ['text', 'audio'],
        tts_vendor: ttsVendor,
        voice_name: voiceName || undefined,
      });

      console.log('Agent invited:', agentResponse);
      console.log('Agent ID received from backend:', agentResponse.agent_id);
      console.log('Setting agent ID state to:', agentResponse.agent_id);
      setAgentId(agentResponse.agent_id);
      console.log('Agent ID state updated');
      setIsConnecting(false);
    } catch (err: any) {
      console.error('Error starting conversation:', err);
      setError(err.response?.data?.detail || 'Failed to start voice conversation');
      setIsConnecting(false);
    }
  };

  // Stop voice conversation
  const handleStopConversation = async () => {
    try {
      console.log('handleStopConversation called');
      console.log('Current agentId state:', agentId);

      if (agentId) {
        console.log('Stopping conversation with agent ID:', agentId);
        await agoraAPI.stopConversation({ agent_id: agentId });
        console.log('Stop conversation API call successful');
      } else {
        console.warn('No agent ID available, skipping stop agent API call');
      }

      // Leave channel
      await client.leave();
      setIsConnected(false);
      setChannelInfo(null);
      setAgentId(null);

      if (onClose) {
        onClose();
      }
    } catch (err: any) {
      console.error('Error stopping conversation:', err);
      setError('Failed to stop conversation');
    }
  };

  // Toggle microphone
  const handleToggleMic = async () => {
    if (localMicrophoneTrack) {
      await localMicrophoneTrack.setEnabled(!micEnabled);
      setMicEnabled(!micEnabled);
    }
  };

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      console.log('VoiceChat unmounting, agentId:', agentId);
      if (agentId) {
        console.log('Stopping agent on cleanup with ID:', agentId);
        agoraAPI.stopConversation({ agent_id: agentId }).catch((error) => {
          console.error('Error stopping agent on cleanup:', error);
        });
      }
    };
  }, [agentId]);

  return (
    <div className="flex flex-col h-full">
      {/* Remote audio players - render for each remote user */}
      {remoteUsers && remoteUsers.length > 0 && remoteUsers.map((user) => {
        if (!user || !user.uid) {
          console.warn('Invalid remote user:', user);
          return null;
        }
        return <RemoteAudioPlayer key={user.uid} user={user} />;
      })}

      {/* Header */}
      <div className="flex items-center justify-between p-4 border-b border-gray-200">
        <h3 className="text-lg font-semibold text-gray-900">Voice Assistant</h3>
        <button
          onClick={onClose}
          className="text-gray-400 hover:text-gray-600"
        >
          <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>
      </div>

      {/* Content */}
      <div className="flex-1 flex flex-col items-center justify-center p-6 space-y-6">
        {error && (
          <div className="w-full p-4 bg-red-50 border border-red-200 rounded-lg">
            <p className="text-sm text-red-600">{error}</p>
          </div>
        )}

        {!channelInfo ? (
          /* Not connected */
          <div className="w-full max-w-md space-y-6">
            <div className="text-center">
              <div className="w-24 h-24 mx-auto bg-blue-100 rounded-full flex items-center justify-center">
                <svg className="w-12 h-12 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 11a7 7 0 01-7 7m0 0a7 7 0 01-7-7m7 7v4m0 0H8m4 0h4m-4-8a3 3 0 01-3-3V5a3 3 0 116 0v6a3 3 0 01-3 3z" />
                </svg>
              </div>
              <p className="mt-4 text-gray-600">
                Start a voice conversation with the AI assistant
              </p>
            </div>

            {/* TTS Configuration */}
            <div className="space-y-4 p-4 bg-gray-50 rounded-lg border border-gray-200">
              <h4 className="text-sm font-semibold text-gray-700">Voice Settings</h4>

              {/* TTS Vendor Selection */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  TTS Provider
                </label>
                <select
                  value={ttsVendor}
                  onChange={(e) => setTtsVendor(e.target.value as 'microsoft' | 'elevenlabs')}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                  disabled={isConnecting}
                >
                  <option value="microsoft">Microsoft Azure TTS</option>
                  <option value="elevenlabs">ElevenLabs</option>
                </select>
              </div>

              {/* Voice Name/ID */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Voice {ttsVendor === 'microsoft' ? 'Name' : 'ID'} (Optional)
                </label>
                <input
                  type="text"
                  value={voiceName}
                  onChange={(e) => setVoiceName(e.target.value)}
                  placeholder={
                    ttsVendor === 'microsoft'
                      ? 'e.g., en-US-JennyNeural'
                      : 'e.g., voice-id-here'
                  }
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                  disabled={isConnecting}
                />
                <p className="mt-1 text-xs text-gray-500">
                  {ttsVendor === 'microsoft'
                    ? 'Default: en-US-AndrewMultilingualNeural'
                    : 'Leave empty to use default voice'}
                </p>
              </div>
            </div>

            {/* Start Button */}
            <button
              onClick={handleStartConversation}
              disabled={isConnecting}
              className="w-full px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors font-medium"
            >
              {isConnecting ? 'Connecting...' : 'Start Voice Chat'}
            </button>
          </div>
        ) : (
          /* Connected */
          <div className="w-full h-full flex flex-col space-y-4">
            {/* Connection Status */}
            <div className="flex items-center justify-between px-4">
              <div className="flex items-center space-x-2">
                <div className={`w-3 h-3 rounded-full ${isConnected ? 'bg-green-500 animate-pulse' : 'bg-yellow-500'}`} />
                <span className="text-sm text-gray-600">
                  {isConnected ? 'Connected to AI Assistant' : 'Waiting for assistant...'}
                </span>
              </div>
              <div className="flex gap-2">
                <button
                  onClick={() => {
                    // Demo: Add sample messages to show UI
                    addTranscriptMessage('user', '这个视频讲的是什么内容？');
                    setTimeout(() => addTranscriptMessage('assistant', '根据视频内容，这个培训主要介绍了如何使用我们的内部系统。视频涵盖了基本操作流程和常见问题解答。'), 1000);
                  }}
                  className="px-3 py-1 text-sm text-blue-600 hover:text-blue-800 hover:bg-blue-50 rounded transition-colors"
                  title="Add demo messages"
                >
                  测试
                </button>
                <button
                  onClick={handleClearTranscript}
                  className="px-3 py-1 text-sm text-gray-600 hover:text-gray-900 hover:bg-gray-100 rounded transition-colors"
                  title="Clear transcript"
                >
                  清空
                </button>
                <button
                  onClick={() => setShowDebug(true)}
                  className="px-3 py-1 text-sm text-purple-600 hover:text-purple-800 hover:bg-purple-50 rounded transition-colors"
                  title="Open debug console"
                >
                  调试
                </button>
              </div>
            </div>

            {/* Audio Enable Button (when autoplay is blocked) */}
            {audioBlocked && (
              <div className="px-4">
                <button
                  onClick={async () => {
                    console.log('[AUDIO ENABLE] User clicked to enable audio');
                    try {
                      // Manually play all remote audio tracks
                      for (const user of remoteUsers) {
                        if (user.audioTrack) {
                          console.log(`[AUDIO ENABLE] Playing audio for user ${user.uid}`);
                          await user.audioTrack.play();
                          console.log(`[AUDIO ENABLE] ✅ Audio enabled for user ${user.uid}`);
                        }
                      }
                      setAudioBlocked(false);
                    } catch (error) {
                      console.error('[AUDIO ENABLE] ❌ Failed to enable audio:', error);
                    }
                  }}
                  className="w-full px-4 py-3 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors font-medium flex items-center justify-center space-x-2"
                >
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15.536 8.464a5 5 0 010 7.072m2.828-9.9a9 9 0 010 12.728M5.586 15H4a1 1 0 01-1-1v-4a1 1 0 011-1h1.586l4.707-4.707C10.923 3.663 12 4.109 12 5v14c0 .891-1.077 1.337-1.707.707L5.586 15z" />
                  </svg>
                  <span>Click to Enable Audio</span>
                </button>
                <p className="text-xs text-gray-600 mt-2 text-center">
                  Your browser blocked audio playback. Click the button above to hear the AI assistant.
                </p>
              </div>
            )}

            {/* Transcript Display - Shows ASR results and AI responses */}
            <div className="flex-1 flex flex-col bg-gray-50 rounded-lg border border-gray-200 overflow-hidden">
              {/* Header - Always visible */}
              <div className="bg-gray-100 px-4 py-2 border-b border-gray-300">
                <p className="text-xs text-gray-700 text-center font-medium">
                  对话记录 - 语音转文字 (ASR) 和 AI 回复
                </p>
              </div>

              {/* Messages area */}
              <div className="flex-1 overflow-y-auto px-4">
                {transcriptMessages.length === 0 ? (
                  <div className="h-full flex items-center justify-center">
                    <div className="text-center">
                      <div className="w-24 h-24 mx-auto bg-blue-100 rounded-full flex items-center justify-center mb-4">
                        <svg className="w-12 h-12 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z" />
                        </svg>
                      </div>
                      <p className="text-gray-600">对话文字记录将显示在此处</p>
                      <p className="text-sm text-gray-500 mt-2">
                        开始说话，系统会自动显示语音转文字和 AI 回复
                      </p>
                    </div>
                  </div>
                ) : (
                  <div className="py-4 space-y-3">
                    {transcriptMessages.map((message) => (
                      <div
                        key={message.id}
                        className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}
                      >
                        <div
                          className={`max-w-[80%] rounded-lg px-4 py-2 ${
                            message.role === 'user'
                              ? 'bg-blue-600 text-white'
                              : 'bg-white text-gray-900 border border-gray-200'
                          }`}
                        >
                          <div className="flex items-center gap-2 mb-1">
                            <span className="text-xs font-semibold opacity-75">
                              {message.role === 'user' ? '用户 (ASR)' : 'AI 助手'}
                            </span>
                            <span className="text-xs opacity-60">
                              {message.timestamp.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit', second: '2-digit' })}
                            </span>
                          </div>
                          <p className="text-sm whitespace-pre-wrap">{message.content}</p>
                        </div>
                      </div>
                    ))}
                    <div ref={transcriptEndRef} />
                  </div>
                )}
              </div>
            </div>

            {/* Microphone Control */}
            <div className="flex items-center justify-center space-x-4 px-4">
              <button
                onClick={handleToggleMic}
                className={`p-4 rounded-full transition-colors ${
                  micEnabled
                    ? 'bg-blue-600 hover:bg-blue-700 text-white'
                    : 'bg-red-600 hover:bg-red-700 text-white'
                }`}
                title={micEnabled ? 'Mute microphone' : 'Unmute microphone'}
              >
                {micEnabled ? (
                  <svg className="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 11a7 7 0 01-7 7m0 0a7 7 0 01-7-7m7 7v4m0 0H8m4 0h4m-4-8a3 3 0 01-3-3V5a3 3 0 116 0v6a3 3 0 01-3 3z" />
                  </svg>
                ) : (
                  <svg className="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5.586 15H4a1 1 0 01-1-1v-4a1 1 0 011-1h1.586l4.707-4.707C10.923 3.663 12 4.109 12 5v14c0 .891-1.077 1.337-1.707.707L5.586 15z" />
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 14l2-2m0 0l2-2m-2 2l-2-2m2 2l2 2" />
                  </svg>
                )}
              </button>

              <button
                onClick={handleStopConversation}
                className="px-6 py-3 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors"
              >
                End Conversation
              </button>
            </div>

            {/* Instructions */}
            <div className="px-4 py-3 bg-blue-50 border border-blue-200 rounded-lg mx-4">
              <p className="text-sm text-blue-800">
                <strong>Note:</strong> Using Agora Conversational AI API for real-time transcript delivery.
                Transcripts are automatically delivered via RTM and rendered word-by-word.
              </p>
            </div>
          </div>
        )}
      </div>

      {/* Debug Panel */}
      <DebugPanel isOpen={showDebug} onClose={() => setShowDebug(false)} />
    </div>
  );
};

// Wrapper component with Agora RTC Provider
const VoiceChat: React.FC<VoiceChatProps> = (props) => {
  return (
    <AgoraRTCProvider client={agoraClient}>
      <VoiceChatInner {...props} />
    </AgoraRTCProvider>
  );
};

export default VoiceChat;
