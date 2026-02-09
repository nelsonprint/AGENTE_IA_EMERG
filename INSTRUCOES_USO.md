# WhatsApp Bot AI - Dashboard de Gerenciamento

## 🎉 Sistema Criado com Sucesso!

Seu app web para gerenciar o chatbot WhatsApp com IA foi criado e está funcionando!

## 📋 O que foi implementado?

### ✅ Funcionalidades Principais

1. **Sistema de Autenticação**
   - Login e registro de usuários admin
   - Segurança com JWT tokens
   - Credenciais iniciais criadas: `admin` / `admin123`

2. **Dashboard Principal**
   - Estatísticas em tempo real
   - Conversas ativas
   - Mensagens do dia
   - Total de usuários
   - Gráficos visuais

3. **Configurações de API Keys**
   - OpenAI API Key (GPT-4o-mini)
   - Evolution API (WhatsApp)
   - Supabase (Banco de dados)
   - Redis (Cache/Memória)
   - Todas as chaves são mascaradas por segurança
   - Toggle para mostrar/ocultar chaves

4. **Editor de Prompts**
   - Criar múltiplos prompts personalizados
   - Editar comportamento do bot
   - Ativar/desativar prompts
   - Apenas um prompt ativo por vez

5. **Monitor de Conversas**
   - Visualizar conversas em tempo real
   - Filtrar por status (Todas, Ativas, Transferidas)
   - Ver histórico completo de mensagens
   - Transferir para atendimento humano
   - Responder manualmente quando transferido
   - Encerrar conversas

6. **Webhook para WhatsApp**
   - Endpoint: `/api/webhook/{webhook_id}`
   - Recebe mensagens da Evolution API
   - Processa com IA automaticamente
   - Detecta keywords para transferência humana
   - Salva histórico no banco de dados

## 🚀 Como Usar

### 1. Acesso Inicial

```
URL: http://seu-dominio.com
Usuário: admin
Senha: admin123
```

**IMPORTANTE**: Altere a senha após o primeiro login!

### 2. Configurar API Keys

1. Acesse "Configurações" no menu lateral
2. Preencha as credenciais necessárias:

   **OpenAI API**
   - Obtenha em: https://platform.openai.com/api-keys
   - Cole sua chave `sk-...`

   **Evolution API (WhatsApp)**
   - URL da sua instância Evolution API
   - API Key fornecida pela Evolution

   **Supabase** (Opcional)
   - URL do seu projeto Supabase
   - Anon Key ou Service Role Key
   - Para salvar usuários e mensagens

   **Redis** (Opcional)
   - URL do Redis (ex: `redis://localhost:6379`)
   - Senha (se houver)
   - Para memória de conversação

3. Clique em "Salvar Configurações"

### 3. Criar Prompts do Bot

1. Acesse "Prompts" no menu
2. Clique em "Novo Prompt"
3. Defina:
   - Nome do prompt (ex: "Atendimento Amigável")
   - Instruções do sistema (ex: "Você é um assistente virtual educado...")
   - Marque "Ativar este prompt"
4. Salve

**Exemplo de Prompt**:
```
Você é um assistente virtual da empresa XYZ. 
Responda de forma educada e prestativa.
Se o cliente pedir para falar com um humano, informe que irá transferir.
Mantenha respostas curtas e objetivas.
```

### 4. Configurar Webhook na Evolution API

Para receber mensagens do WhatsApp, configure o webhook na Evolution API:

```
URL do Webhook: https://seu-dominio.com/api/webhook/seu-id-unico
Método: POST
```

O webhook irá:
- Receber mensagens dos usuários
- Processar com IA (usando seu prompt ativo)
- Responder automaticamente
- Detectar pedidos de transferência humana
- Salvar todo histórico

### 5. Monitorar Conversas

1. Acesse "Conversas" no menu
2. Veja todas as conversas em tempo real
3. Clique em uma conversa para ver detalhes
4. Ações disponíveis:
   - **Transferir**: Move para atendimento humano (bot para de responder)
   - **Responder**: Envie mensagens manualmente (quando transferido)
   - **Encerrar**: Fecha a conversa

### 6. Atendimento Humano

Quando uma conversa é transferida:
1. O bot para de responder automaticamente
2. Aparece um campo de texto para você digitar
3. Suas mensagens são marcadas como "Agente"
4. O usuário recebe suas respostas via WhatsApp

## 🔧 Tecnologias Utilizadas

### Backend
- FastAPI (Python)
- MongoDB (banco de dados principal)
- OpenAI GPT-4o-mini (via Emergent LLM Key)
- Emergentintegrations (biblioteca para IA)
- Redis (opcional - cache)
- Supabase (opcional - dados externos)

### Frontend
- React 19
- React Router (navegação)
- Shadcn/UI (componentes)
- Recharts (gráficos)
- Tailwind CSS (estilização)
- Design dark mode profissional

## 📊 Fluxo de Funcionamento

```
1. Usuário → WhatsApp → Evolution API
2. Evolution API → Webhook → Seu Sistema
3. Sistema → Verifica se transferido para humano
4. Se NÃO transferido:
   - Processa com OpenAI
   - Responde automaticamente
5. Se SIM transferido:
   - Aguarda resposta do agente humano
6. Histórico salvo no MongoDB
```

## 🔐 Segurança

- Todas as senhas são hasheadas com bcrypt
- JWT tokens para autenticação
- API keys mascaradas no frontend
- CORS configurado
- MongoDB local sem exposição externa

## ⚠️ Importante

### Keywords de Transferência

O bot detecta automaticamente estas palavras para transferir:
- "falar com atendente"
- "atendente humano"
- "falar com alguém"
- "preciso de ajuda humana"
- "transferir"
- "humano"

Você pode modificar isso em `/app/backend/bot_service.py`

### Custos

- **OpenAI**: Você paga por uso (tokens)
- **Emergent LLM Key**: Alternativa com créditos Emergent
- **Evolution API**: Confira o plano contratado
- **Supabase**: Plano free disponível
- **Redis**: Pode usar local gratuito

## 🎨 Personalização

### Alterar Cores/Design

Edite `/app/frontend/src/index.css`:
```css
--primary: 142 76% 36%; /* Verde WhatsApp */
--ai-accent: 262 83% 58%; /* Roxo para IA */
```

### Adicionar Novos Prompts

Use o dashboard, mas se quiser criar via código:
```javascript
POST /api/prompts
{
  "name": "Prompt Personalizado",
  "system_prompt": "Suas instruções aqui...",
  "is_active": true
}
```

## 🐛 Troubleshooting

**Bot não responde?**
- Verifique se a OpenAI API Key está configurada
- Confirme que há um prompt ativo
- Veja os logs: `tail -f /var/log/supervisor/backend.err.log`

**Webhook não recebe mensagens?**
- Confirme a URL do webhook na Evolution API
- Teste manualmente: `curl -X POST https://seu-dominio.com/api/webhook/test -d '{}'`

**Frontend não carrega?**
- Verifique: `sudo supervisorctl status`
- Reinicie: `sudo supervisorctl restart frontend backend`

## 📞 Suporte

Para dúvidas sobre:
- **Emergent Platform**: Documentação Emergent
- **Evolution API**: https://evolution-api.com/
- **OpenAI**: https://platform.openai.com/docs

## 🎯 Próximos Passos Sugeridos

1. **Configurar suas API Keys reais** nas Configurações
2. **Criar prompts personalizados** para seu negócio
3. **Testar o webhook** enviando uma mensagem teste
4. **Adicionar mais agentes** criando novos usuários admin
5. **Implementar analytics** para métricas avançadas
6. **Integrar com CRM** usando os endpoints de API

---

**✨ Seu chatbot WhatsApp com IA está pronto para uso!**

Acesse agora: http://localhost:3000
