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

## Architecture
```
/app
├── backend/
│   ├── server.py          # FastAPI main application
│   ├── bot_service.py     # AI/LLM service with name placeholder replacement
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
- **Frontend:** React.js
- **Database:** MongoDB (local), Supabase (optional via settings)
- **Cache:** Redis (optional, for conversation memory)
- **AI:** OpenAI GPT-4o-mini via emergentintegrations
- **WhatsApp:** Evolution API

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

### P0 Feature - Dynamic Name Substitution (Completed Feb 9, 2026)
- [x] Extract customer name (`pushName`) from Evolution API webhook
- [x] Replace placeholders in prompts with customer's actual name
- Supported placeholders:
  - `[Nome do Proprietário]`
  - `[Nome do Cliente]`
  - `[customer_name]`
  - `[nome]`
  - `{nome}`
  - `{customer_name}`
  - `{{nome}}`
  - `{{customer_name}}`
- Falls back to "Cliente" if name is unavailable

## API Endpoints
- `POST /api/auth/register` - User registration
- `POST /api/auth/login` - User login
- `GET/PUT /api/settings` - Manage settings
- `GET/POST/PUT/DELETE /api/prompts` - Manage prompts
- `GET /api/prompts/active` - Get active prompt
- `GET /api/conversations` - List conversations
- `POST /api/conversations/{id}/transfer` - Transfer to human
- `POST /api/webhook/{webhook_id}` - Receive Evolution API webhooks
- `GET/POST/DELETE /api/evolution-instances` - Manage instances

## Backlog

### P1 - High Priority
- [ ] Real-time conversation monitoring (WebSockets/polling)
- [ ] Improved human handoff workflow

### P2 - Medium Priority
- [ ] Enhanced prompt management UX
- [ ] Conversation analytics

### P3 - Low Priority
- [ ] Multi-language support
- [ ] Bulk message sending

## Usage Notes
To use dynamic name in prompts, include any of the supported placeholders in your prompt text. Example:
```
Olá [Nome do Proprietário], sou um assistente virtual da Lucro Líquido. Como posso ajudá-lo?
```
