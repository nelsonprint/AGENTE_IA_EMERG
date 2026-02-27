# WhatsApp Bot Management Platform - PRD

## Original Problem Statement
Build a complete web application to replace and enhance an existing N8N automation for a WhatsApp bot with:
- Login/password system
- Dashboard to manage API keys (OpenAI, Evolution API, Supabase, Redis)
- Dashboard to create and manage custom AI prompts
- LLM: GPT-4o-mini (OpenAI)
- Database: Supabase
- Real-time conversation monitoring
- Conversation history
- Panel for human agent transfer
- Webhook integration with Evolution API
- Support for multiple Evolution API instances
- AI conversation memory
- Dynamic customer name insertion in prompts
- Notification system with keyword detection

## Architecture
```
/app
├── backend/
│   ├── server.py          # FastAPI main application
│   ├── bot_service.py     # AI/LLM service with keyword detection
│   ├── evolution_service.py # Evolution API integration
│   ├── redis_service.py   # Redis session management
│   ├── supabase_service.py # Supabase connection
│   ├── auth.py           # JWT authentication
│   └── models.py         # Pydantic models
├── frontend/
│   └── src/
│       ├── pages/        # React pages (Login, Dashboard, etc.)
│       └── components/   # Shared components
```

## Tech Stack
- **Backend:** FastAPI, Python, Motor (MongoDB async driver)
- **Frontend:** React.js, Tailwind CSS, Shadcn/UI
- **Database:** MongoDB (local), Supabase (optional via settings)
- **Cache:** Redis (optional, for conversation memory)
- **AI:** OpenAI GPT-4o-mini via emergentintegrations
- **WhatsApp:** Evolution API
- **Timezone:** America/Sao_Paulo

## Implemented Features (Feb 2026)

### Core Features
- [x] User authentication (JWT)
- [x] Settings management (API keys via dashboard)
- [x] Prompt management (CRUD)
- [x] Evolution API instance management (multiple instances)
- [x] Webhook endpoint for receiving WhatsApp messages
- [x] AI response generation with conversation history
- [x] Message sending via Evolution API
- [x] Conversation listing and history
- [x] Human transfer detection
- [x] Dashboard statistics
- [x] Delete conversations

### P0 Feature - Keyword Notification System (Completed Feb 27, 2026)
- [x] Custom keyword management via UI (add/remove keywords)
- [x] Keyword detection in incoming messages
- [x] WhatsApp notification to owner when keyword detected
- [x] Notification includes customer name and last 3 messages
- [x] Two modes: 
  - Single notification per conversation (default)
  - Notify on every keyword detection (optional toggle)
- [x] Reset notification status button in conversation view
- [x] Visual indicator (bell icon) for notified conversations
- [x] **89 custom keywords configured** by user

### Dynamic Name Substitution
- [x] Extract customer name (`pushName`) from Evolution API webhook
- [x] Replace placeholders in prompts with customer's actual name
- [x] Falls back to "Cliente" if name is unavailable

### Bot/Menu Detection
- [x] Auto-detect numbered menus from other bots
- [x] Smart department selection (Administrativo, Financeiro, etc.)
- [x] Name request detection and auto-response

## API Endpoints
- `POST /api/auth/register` - User registration
- `POST /api/auth/login` - User login
- `GET/PUT /api/settings` - Manage settings (includes transfer_keywords, notify_every_keyword)
- `GET/POST/PUT/DELETE /api/prompts` - Manage prompts
- `GET /api/prompts/active` - Get active prompt
- `GET /api/conversations` - List conversations
- `GET /api/conversations/{id}` - Get single conversation
- `POST /api/conversations/{id}/transfer` - Transfer to human
- `POST /api/conversations/{id}/close` - Close conversation
- `DELETE /api/conversations/{id}` - Delete conversation
- `POST /api/conversations/{id}/reset-notification` - Reset notification status
- `POST /api/webhook/{webhook_id}` - Receive Evolution API webhooks
- `POST /api/send-message` - Send manual message
- `GET/POST/DELETE /api/evolution-instances` - Manage instances
- `POST /api/evolution-instances/{id}/set-default` - Set default instance
- `POST /api/evolution-instances/{id}/test` - Test instance connection

## Data Models

### Settings
```python
{
  notification_whatsapp: str,      # Phone to receive notifications
  transfer_keywords: List[str],    # Custom keywords for transfer
  notify_every_keyword: bool,      # If True, notify on every keyword
  openai_api_key: str,
  evolution_api_url: str,
  evolution_api_key: str,
  ...
}
```

### Conversation
```python
{
  id: str,
  phone_number: str,
  user_name: str,
  status: str,  # active, transferred, closed
  notified_owner: bool,  # True if notification was sent
  messages: List[Message],
  ...
}
```

## Backlog

### P1 - High Priority
- [ ] Implement `indice_contato` logic (rotate 5 opening messages)
- [ ] Refactor monolithic server.py into service modules

### P2 - Medium Priority  
- [ ] WebSocket for real-time conversation updates
- [ ] Full human handoff UI (claim conversation, pause bot)

### P3 - Low Priority
- [ ] Conversation analytics
- [ ] Multi-language support

## Testing Credentials
- **User:** admin
- **Password:** admin123
