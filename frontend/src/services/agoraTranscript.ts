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
export function parseTranscriptMessage(messageData: any): TranscriptItem | null {
  console.log('[Parser] ===== parseTranscriptMessage called =====');
  console.log('[Parser] Input type:', typeof messageData);
  console.log('[Parser] Input value:', messageData);

  try {
    // If message is a string, parse it as JSON
    let data: TranscriptionMessage;
    if (typeof messageData === 'string') {
      console.log('[Parser] Parsing string as JSON');
      data = JSON.parse(messageData) as TranscriptionMessage;
      console.log('[Parser] Parsed JSON:', data);
    } else if (messageData instanceof Uint8Array) {
      console.log('[Parser] Converting Uint8Array to string');
      const decoder = new TextDecoder();
      const messageString = decoder.decode(messageData);
      console.log('[Parser] Decoded string:', messageString);
      data = JSON.parse(messageString) as TranscriptionMessage;
      console.log('[Parser] Parsed JSON:', data);
    } else {
      console.log('[Parser] Using data as-is (already an object)');
      data = messageData as TranscriptionMessage;
    }

    console.log('[Parser] Message object type:', data.object);
    console.log('[Parser] Message text:', data.text);

    // Only process transcription messages
    if (
      data.object !== TranscriptMessageType.USER_TRANSCRIPTION &&
      data.object !== TranscriptMessageType.AGENT_TRANSCRIPTION
    ) {
      console.log('[Parser] ⏭️  Skipping non-transcription message type:', data.object);
      return null;
    }

    const isUser = data.object === TranscriptMessageType.USER_TRANSCRIPTION;
    console.log('[Parser] Is user message:', isUser);

    const status = isUser
      ? ((data as IUserTranscription).final ? TurnStatus.END : TurnStatus.IN_PROGRESS)
      : (data as IAgentTranscription).turn_status;
    console.log('[Parser] Message status:', status);

    const result = {
      id: `${data.turn_id}-${data.user_id}-${data.start_ms}`,
      uid: data.user_id,
      turn_id: data.turn_id,
      timestamp: Date.now(),
      text: data.text.trim(),
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
