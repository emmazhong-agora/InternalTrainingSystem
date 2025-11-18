# Conversational AI API Integration Guide

## Overview
This API provides transcript delivery via Agora RTM (Real-Time Messaging) instead of requiring direct RTM management in your components.

## Prerequisites
- Agora RTC SDK v4.5.1 or later
- Agora RTM SDK integrated
- Backend configured with `enable_rtm: true` and `data_channel: "rtm"` ✅ (Already configured)

## Key Features
- Automatic transcript management via RTM
- Word-by-word or sentence rendering modes
- Agent state tracking
- Metrics and error handling
- Event-based architecture

## Integration Steps

### 1. Enable RTC Audio PTS Metadata
**IMPORTANT**: Must be called BEFORE creating RTC client:

```typescript
import AgoraRTC from 'agora-rtc-sdk-ng';

// Enable audio PTS metadata - REQUIRED for transcripts
AgoraRTC.setParameter("ENABLE_AUDIO_PTS_METADATA", true);

// Then create client
const agoraClient = AgoraRTC.createClient({
  mode: 'rtc',
  codec: 'vp8',
});
```

### 2. Initialize Conversational AI API

```typescript
import { ConversationalAIAPI } from '../conversational-ai-api';
import { EConversationalAIAPIEvents, ETranscriptHelperMode } from '../conversational-ai-api/type';

// After RTC and RTM are connected
const conversationalAIAPI = ConversationalAIAPI.init({
  rtcEngine: agoraClient,
  rtmEngine: rtmClient,
  renderMode: ETranscriptHelperMode.WORD, // or TEXT for sentence mode
});
```

### 3. Subscribe to Transcript Events

```typescript
const handleTranscriptUpdate = (transcripts) => {
  console.log('Transcripts updated:', transcripts);
  // transcripts is an array of ITranscriptHelperItem
  // Each item has: uid, text, status, turn_id, metadata
  setMessages(transcripts.map(t => ({
    role: Number(t.uid) === 0 ? 'user' : 'assistant',
    content: t.text,
    timestamp: new Date(t._time),
  })));
};

conversationalAIAPI.on(
  EConversationalAIAPIEvents.TRANSCRIPT_UPDATED,
  handleTranscriptUpdate
);
```

### 4. Subscribe to Channel Messages

```typescript
// Must be called before agent starts
conversationalAIAPI.subscribeMessage(channelName);
```

### 5. Cleanup

```typescript
// On component unmount
conversationalAIAPI.unsubscribe();
conversationalAIAPI.destroy();
```

## Complete Example

```typescript
useEffect(() => {
  let conversationalAIAPI: any = null;

  const init = async () => {
    // 1. Enable PTS metadata
    AgoraRTC.setParameter("ENABLE_AUDIO_PTS_METADATA", true);

    // 2. Join RTC
    await agoraClient.join(appId, channel, rtcToken, uid);

    // 3. Login to RTM
    const rtmClient = AgoraRTM.createInstance(appId);
    await rtmClient.login({ token: rtmToken, uid: uid.toString() });

    // 4. Initialize API
    conversationalAIAPI = ConversationalAIAPI.init({
      rtcEngine: agoraClient,
      rtmEngine: rtmClient,
      renderMode: ETranscriptHelperMode.WORD,
    });

    // 5. Subscribe to transcripts
    conversationalAIAPI.on(
      EConversationalAIAPIEvents.TRANSCRIPT_UPDATED,
      handleTranscriptUpdate
    );

    // 6. Subscribe to channel
    conversationalAIAPI.subscribeMessage(channel);
  };

  init();

  return () => {
    conversationalAIAPI?.unsubscribe();
    conversationalAIAPI?.destroy();
  };
}, []);
```

## Event Types

### TRANSCRIPT_UPDATED
Returns complete transcript history array. Each update may modify recent items.

```typescript
interface ITranscriptHelperItem {
  uid: string;           // User ID ("0" for user, agent UID for assistant)
  text: string;          // Transcript text
  status: ETurnStatus;   // IN_PROGRESS, END, or INTERRUPTED
  turn_id: number;       // Conversation turn ID
  _time: number;         // Timestamp
  metadata: object;      // Original transcript data
}
```

### AGENT_STATE_CHANGED
Agent state transitions: `idle`, `listening`, `thinking`, `speaking`, `silent`

### AGENT_METRICS
Performance metrics from LLM, TTS, etc.

### AGENT_ERROR
Error events from various agent modules

## Transcript Status

```typescript
enum ETurnStatus {
  IN_PROGRESS = 0,  // Still being transcribed
  END = 1,          // Transcription complete
  INTERRUPTED = 2   // User interrupted agent
}
```

## Backend Configuration (Already Done ✅)

```python
"advanced_features": {
    "enable_rtm": True  # Enable RTM for transcript delivery
},
"parameters": {
    "data_channel": "rtm"  # Use RTM as data channel for transcripts
}
```

## Important Notes

1. **PTS Metadata**: Must enable `ENABLE_AUDIO_PTS_METADATA` before creating RTC client
2. **Transcript Updates**: Events return the COMPLETE history, not just new messages
3. **UID Matching**: User messages have `uid: "0"`, agent messages have `uid: "{agent_rtc_uid}"`
4. **Cleanup**: Always call `unsubscribe()` and `destroy()` on unmount
5. **RTM Not Needed**: You don't need to manually handle RTM messages anymore - the API does it

## Removed Code

You can now remove:
- Direct RTM message listeners
- `parseTranscriptMessage` utilities
- Manual transcript aggregation logic
- RTM channel subscribe/unsubscribe management

The Conversational AI API handles all of this internally!
