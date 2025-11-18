# Phase 2: Service Refactoring & Admin UI - Implementation Summary

## Current Status

✅ **Phase 1 Complete**: Unified Prompt Management System
- Database layer, API layer, service layer all working
- 7 prompts successfully seeded
- API endpoints tested and functional

## Phase 2 Tasks

### Part 1: Service Refactoring

#### Changes Required for Chat Service (`app/services/ai_chat_service.py`)

**Step 1**: Update imports and __init__
```python
from sqlalchemy.orm import Session
from app.services.prompt_service import prompt_service

class AIChatService:
    def __init__(self):
        self.openai_client = OpenAI(api_key=settings.OPENAI_API_KEY)
        # Remove: self.system_prompt = self._build_system_prompt()
```

**Step 2**: Update ask_question method
```python
def ask_question(
    self,
    db: Session,  # ADD THIS PARAMETER
    video_id: int,
    question: str,
    ...
):
    # Replace hardcoded prompt with:
    prompt_config = prompt_service.render_prompt(
        db=db,
        prompt_name="chat_qa_main",
        variables={}
    )

    messages = [
        {"role": "system", "content": prompt_config["system_message"]}
    ]

    # Use prompt config for API call:
    response = self.openai_client.chat.completions.create(
        model=prompt_config["model"],
        temperature=prompt_config["temperature"],
        max_tokens=prompt_config["max_tokens"],
        messages=messages
    )
```

**Step 3**: Update _generate_context_prompt method
```python
def _generate_context_prompt(
    self,
    db: Session,  # ADD THIS
    context_chunks: List[Dict],
    timestamp: float
) -> str:
    current_content = context_chunks[0]['text'][:200]

    # Use centralized prompt
    prompt_config = prompt_service.render_prompt(
        db=db,
        prompt_name="chat_context_engagement",
        variables={
            "timestamp": int(timestamp),
            "current_content": current_content
        }
    )

    messages = [
        {"role": "system", "content": prompt_config["system_message"]},
        {"role": "user", "content": prompt_config["user_message"]}
    ]

    response = self.openai_client.chat.completions.create(
        model=prompt_config["model"],
        temperature=prompt_config["temperature"],
        max_tokens=prompt_config["max_tokens"],
        messages=messages
    )
```

**Step 4**: Update generate_quiz method
```python
def generate_quiz(
    self,
    db: Session,  # ADD THIS
    video_id: int,
    current_timestamp: Optional[float] = None,
    difficulty: str = "medium"
) -> Dict:
    # Get context...

    prompt_config = prompt_service.render_prompt(
        db=db,
        prompt_name="quiz_generation",
        variables={
            "difficulty": difficulty,
            "context_text": context_text
        }
    )

    messages = [
        {"role": "system", "content": prompt_config["system_message"]},
        {"role": "user", "content": prompt_config["user_message"]}
    ]

    response = self.openai_client.chat.completions.create(
        model=prompt_config["model"],
        temperature=prompt_config["temperature"],
        max_tokens=prompt_config["max_tokens"],
        messages=messages,
        response_format={"type": "json_object"} if prompt_config["response_format"] == "json" else None
    )
```

**Step 5**: Update generate_session_title method
```python
def generate_session_title(
    self,
    db: Session,  # ADD THIS
    first_question: str
) -> str:
    prompt_config = prompt_service.render_prompt(
        db=db,
        prompt_name="chat_session_title",
        variables={"first_question": first_question}
    )

    # Rest of implementation...
```

**Step 6**: Update analyze_video_content method
```python
def analyze_video_content(
    self,
    db: Session,  # ADD THIS
    video_id: int,
    transcript_text: str
) -> Dict:
    prompt_config = prompt_service.render_prompt(
        db=db,
        prompt_name="video_content_analysis",
        variables={"transcript_text": transcript_text[:15000]}
    )

    # Rest of implementation...
```

#### Changes Required for Chat Routes (`app/api/routes/chat.py`)

All endpoints that use `ai_chat_service` need to pass `db` parameter:

```python
@router.post("/ask", response_model=AskQuestionResponse)
async def ask_question(
    request: AskQuestionRequest,
    db: Session = Depends(get_db),  # ADD THIS
    current_user: User = Depends(get_current_user)
):
    answer, chunks, confidence, context_prompt = ai_chat_service.ask_question(
        db=db,  # ADD THIS
        video_id=request.video_id,
        question=request.question,
        ...
    )
```

#### Changes Required for Voice AI (`app/api/routes/agora.py`)

**Update invite_agent endpoint**:
```python
@router.post("/invite-agent", response_model=InviteAgentResponse)
async def invite_agent(
    request: InviteAgentRequest,
    db: Session = Depends(get_db)  # ADD THIS
):
    # Get base voice prompt
    base_prompt_config = prompt_service.render_prompt(
        db=db,
        prompt_name="voice_agent_base",
        variables={}
    )

    system_messages = [
        {"text": base_prompt_config["system_message"]}
    ]

    # If video_id provided, add knowledge context
    if request.video_id:
        # Retrieve chunks...
        knowledge_context = format_chunks_for_voice(chunks)

        knowledge_prompt_config = prompt_service.render_prompt(
            db=db,
            prompt_name="voice_agent_knowledge",
            variables={"knowledge_context": knowledge_context}
        )

        system_messages.append({
            "text": knowledge_prompt_config["system_message"]
        })

    # Build request body with prompt config
    request_body = {
        "llm": {
            "system_messages": system_messages,
            "model": base_prompt_config["model"],
            "temperature": base_prompt_config["temperature"],
            "max_tokens": base_prompt_config["max_tokens"],
            "top_p": base_prompt_config.get("top_p", 1.0)
        },
        ...
    }
```

### Part 2: Admin UI for Prompt Management

#### Frontend Structure

Create in `/frontend/src/pages/admin/`:

1. **PromptsListPage.tsx** - List all prompts
2. **PromptEditorPage.tsx** - Create/edit prompts
3. **PromptTestPage.tsx** - Test prompts with variable preview

#### PromptsList Page Features

```typescript
// Key Features:
- Table view of all prompts
- Filter by category (chat, quiz, voice_ai, analysis)
- Search by name/description
- Quick actions: Edit, Deactivate, Test
- Pagination
- Usage statistics display
```

#### PromptEditor Page Features

```typescript
// Key Features:
- Form to edit prompt fields
- Variable syntax highlighting {variable_name}
- Real-time preview with sample variables
- Model/temperature/max_tokens configuration
- JSON schema editor for structured outputs
- Version management
- Save/Cancel actions
```

#### API Integration

```typescript
// services/promptsAPI.ts
export const promptsAPI = {
  list: (params) => api.get('/api/v1/prompts/', { params }),
  getById: (id) => api.get(`/api/v1/prompts/${id}`),
  getByName: (name) => api.get(`/api/v1/prompts/name/${name}`),
  create: (data) => api.post('/api/v1/prompts/', data),
  update: (id, data) => api.put(`/api/v1/prompts/${id}`, data),
  delete: (id) => api.delete(`/api/v1/prompts/${id}`),
  render: (promptName, variables) =>
    api.post('/api/v1/prompts/render', { prompt_name: promptName, variables }),
  getByCategory: (category) => api.get(`/api/v1/prompts/category/${category}`)
};
```

## Implementation Priority

### High Priority (Do First):
1. ✅ Refactor `ask_question` method in Chat service
2. ✅ Update chat routes to pass `db` parameter
3. ⬜ Test Chat Q&A functionality works with centralized prompts

### Medium Priority:
4. ⬜ Refactor other Chat service methods (quiz, title, analysis)
5. ⬜ Refactor Voice AI service
6. ⬜ Test all refactored services

### Low Priority (Can do later):
7. ⬜ Build Admin UI - Prompts List page
8. ⬜ Build Admin UI - Prompt Editor page
9. ⬜ Build Admin UI - Prompt Test page

## Testing Checklist

After refactoring:

- [ ] Chat Q&A still works (test via frontend)
- [ ] Context engagement prompts generated correctly
- [ ] Quiz generation works
- [ ] Session titles generated
- [ ] Video analysis works
- [ ] Voice AI base prompt works
- [ ] Voice AI knowledge context works
- [ ] All prompts use correct model/temperature from database
- [ ] Prompt usage statistics increment correctly

## Benefits Achieved

Once complete:

1. **No more code deployments for prompt changes** - Update via API/UI
2. **A/B testing ready** - Create multiple versions, toggle is_default
3. **Analytics** - Track which prompts are used most
4. **Version control** - Keep history of prompt iterations
5. **Team collaboration** - Non-technical team members can edit prompts

## Next Steps

**Immediate**: Complete service refactoring before building Admin UI
**Reason**: Need to validate that centralized prompts work correctly in production flow

---

**Implementation Date**: 2025-11-14
**Status**: Phase 2 In Progress
**Estimated Time**: 2-3 hours for refactoring, 4-6 hours for Admin UI
