/**
 * Agora Transcript Service
 *
 * Handles real-time transcript messages from Agora Conversational AI agent
 * Based on Agora's Conversational AI Demo implementation
 */

export enum TranscriptMessageType {
  USER_TRANSCRIPTION = 'user.transcription',
  AGENT_TRANSCRIPTION = 'assistant.transcription',
}

export enum TurnStatus {
  IN_PROGRESS = 0,
  END = 1,
  INTERRUPTED = 2,
}

export interface IUserTranscription {
  object: TranscriptMessageType.USER_TRANSCRIPTION;
  text: string;
  start_ms: number;
  duration_ms: number;
  language: string;
  turn_id: number;
  stream_id: number;
  user_id: string;
  final: boolean;
}

export interface IAgentTranscription {
  object: TranscriptMessageType.AGENT_TRANSCRIPTION;
  text: string;
  start_ms: number;
  duration_ms: number;
  language: string;
  turn_id: number;
  stream_id: number;
  user_id: string;
  turn_seq_id: number;
  turn_status: TurnStatus;
}

export type TranscriptionMessage = IUserTranscription | IAgentTranscription;

type TranscriptRecord = Partial<IUserTranscription> & Partial<IAgentTranscription>;

export interface TranscriptItem {
  id: string;
  uid: string;
  turn_id: number;
  timestamp: number;
  text: string;
  status: TurnStatus;
  type: 'user' | 'assistant';
}

/**
 * Parse Agora RTM message into transcript item
 *
 * RTM messages come as plain JSON objects or strings
 */
function decodeMessagePayload(messageData: unknown): unknown {
  if (typeof messageData === 'string') {
    return JSON.parse(messageData);
  }
  if (messageData instanceof Uint8Array) {
    const decoder = new TextDecoder();
    const messageString = decoder.decode(messageData);
    return JSON.parse(messageString);
  }
  return messageData;
}

function isTranscriptionRecord(value: unknown): value is TranscriptRecord {
  if (!value || typeof value !== 'object') {
    return false;
  }
  const candidate = value as TranscriptRecord;
  return (
    typeof candidate.object === 'string' &&
    typeof candidate.text === 'string' &&
    typeof candidate.turn_id === 'number' &&
    typeof candidate.user_id === 'string'
  );
}

export function parseTranscriptMessage(messageData: unknown): TranscriptItem | null {
  console.log('[Parser] ===== parseTranscriptMessage called =====');
  console.log('[Parser] Input type:', typeof messageData);
  console.log('[Parser] Input value:', messageData);

  try {
    // If message is a string, parse it as JSON
    const decoded = decodeMessagePayload(messageData);
    if (!isTranscriptionRecord(decoded)) {
      console.log('[Parser] ⏭️  Skipping message that does not match transcript schema');
      return null;
    }
    const data = decoded;
    const { object, text, turn_id, user_id } = data;

    if (
      typeof object !== 'string' ||
      typeof text !== 'string' ||
      typeof turn_id !== 'number' ||
      typeof user_id !== 'string'
    ) {
      console.log('[Parser] ⏭️  Missing required transcript fields');
      return null;
    }

    console.log('[Parser] Message object type:', object);
    console.log('[Parser] Message text:', text);

    // Only process transcription messages
    if (
      object !== TranscriptMessageType.USER_TRANSCRIPTION &&
      object !== TranscriptMessageType.AGENT_TRANSCRIPTION
    ) {
      console.log('[Parser] ⏭️  Skipping non-transcription message type:', object);
      return null;
    }

    const isUser = object === TranscriptMessageType.USER_TRANSCRIPTION;
    console.log('[Parser] Is user message:', isUser);

    const status = isUser
      ? (data.final ? TurnStatus.END : TurnStatus.IN_PROGRESS)
      : (typeof data.turn_status === 'number' ? data.turn_status : TurnStatus.IN_PROGRESS);
    console.log('[Parser] Message status:', status);

    const result = {
      id: `${turn_id}-${user_id}-${data.start_ms}`,
      uid: user_id,
      turn_id,
      timestamp: Date.now(),
      text: text.trim(),
      status,
      type: isUser ? 'user' as const : 'assistant' as const,
    };

    console.log('[Parser] ✅ Successfully created transcript item:', result);
    return result;
  } catch (error) {
    console.error('[Parser] ❌ Failed to parse message:', error);
    console.error('[Parser] Error type:', (error as Error).name);
    console.error('[Parser] Error message:', (error as Error).message);
    console.error('[Parser] Error stack:', (error as Error).stack);
    return null;
  }
}

/**
 * Check if transcript is complete (not in progress)
 */
export function isTranscriptComplete(item: TranscriptItem): boolean {
  return item.status === TurnStatus.END || item.status === TurnStatus.INTERRUPTED;
}

/**
 * Format turn status for display
 */
export function formatTurnStatus(status: TurnStatus): string {
  switch (status) {
    case TurnStatus.IN_PROGRESS:
      return '进行中...';
    case TurnStatus.INTERRUPTED:
      return '已中断';
    case TurnStatus.END:
    default:
      return '';
  }
}
