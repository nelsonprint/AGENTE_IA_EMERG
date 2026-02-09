# 🎯 GUIA RÁPIDO: Como Configurar o Webhook

## ✅ Sua URL do Webhook

```
https://seu-dominio.com/api/webhook/SEU-ID-PERSONALIZADO
```

**Exemplo:**
```
https://seu-dominio.com/api/webhook/meu-bot-whatsapp
```

---

## 📱 Passo a Passo Completo

### 1️⃣ Configure suas Credenciais

Vá em **Configurações** no dashboard e preencha:

- ✅ **OpenAI API Key** → Sua chave da OpenAI
- ✅ **Evolution API URL** → URL da sua instância Evolution
- ✅ **Evolution API Key** → Chave da Evolution API
- ✅ **Nome da Instância** → Nome da instância (geralmente "default")

Clique em **"Salvar Configurações"**

---

### 2️⃣ Crie um Prompt para o Bot

Vá em **Prompts** e clique em **"Novo Prompt"**:

```
Nome: Atendimento Amigável

Prompt do Sistema:
Você é um assistente virtual da empresa XYZ.
Responda de forma educada e prestativa.
Se o cliente pedir para falar com um humano, informe que irá transferir.
Mantenha respostas curtas e objetivas.
```

Marque ☑️ **"Ativar este prompt"** e salve.

---

### 3️⃣ Configure o Webhook na Evolution API

#### Opção A: Via Painel Evolution API

1. Acesse seu painel Evolution API
2. Selecione sua instância
3. Vá em "Webhook"
4. Cole a URL do webhook (veja na página "Webhook" do dashboard)
5. Ative o evento: **MESSAGES_UPSERT**
6. Salve

#### Opção B: Via API (cURL)

```bash
curl -X POST 'https://sua-evolution-api.com/webhook/set/sua-instancia' \
  -H 'apikey: SUA-API-KEY' \
  -H 'Content-Type: application/json' \
  -d '{
    "webhook": {
      "url": "https://seu-dominio.com/api/webhook/meu-bot-whatsapp",
      "webhook_by_events": false,
      "webhook_base64": false,
      "events": ["MESSAGES_UPSERT"]
    }
  }'
```

---

### 4️⃣ Teste o Webhook

#### Via WhatsApp (Teste Real)
1. Envie uma mensagem para o número conectado na Evolution API
2. Vá em **"Conversas"** no dashboard
3. A conversa deve aparecer automaticamente
4. O bot responderá usando o prompt configurado

#### Via cURL (Teste Manual)

Use o comando disponível na página **"Webhook"** do dashboard:

```bash
curl -X POST 'https://seu-dominio.com/api/webhook/meu-bot-whatsapp' \
  -H 'Content-Type: application/json' \
  -d '{
    "data": {
      "key": {
        "remoteJid": "5511999999999@s.whatsapp.net",
        "fromMe": false
      },
      "message": {
        "conversation": "Olá, preciso de ajuda!"
      },
      "messageTimestamp": 1234567890
    },
    "sender": "5511999999999@s.whatsapp.net",
    "pushName": "João Silva"
  }'
```

---

## 🔄 Como Funciona (Fluxo Completo)

```
1. Cliente envia mensagem no WhatsApp
   ↓
2. Evolution API recebe a mensagem
   ↓
3. Evolution chama seu webhook:
   https://seu-dominio.com/api/webhook/meu-bot-whatsapp
   ↓
4. Sistema processa:
   - Salva conversa no MongoDB
   - Verifica se está transferido para humano
   - Se não: processa com OpenAI (seu prompt ativo)
   - Se sim: aguarda resposta manual do agente
   ↓
5. Bot responde automaticamente via Evolution API
   ↓
6. Cliente recebe resposta no WhatsApp
   ↓
7. Tudo aparece em "Conversas" no dashboard
```

---

## 🎯 Transferência para Humano

### Automática (via keywords)

Quando o cliente digitar:
- "falar com atendente"
- "atendente humano"
- "falar com alguém"
- "preciso de ajuda humana"
- "transferir"
- "humano"

→ O bot para de responder automaticamente
→ Status muda para "Transferido"
→ Você pode responder manualmente em "Conversas"

### Manual

1. Vá em "Conversas"
2. Selecione a conversa
3. Clique em "Transferir"
4. Digite sua mensagem e clique em "Enviar"

---

## ⚙️ Configurações Importantes

### Evolution API

**Nome da Instância**: Geralmente é "default", mas pode ser personalizado na Evolution API.

Para verificar suas instâncias:
```bash
curl -X GET 'https://sua-evolution-api.com/instance/fetchInstances' \
  -H 'apikey: SUA-API-KEY'
```

### OpenAI

**Modelo usado**: GPT-4o-mini (rápido e econômico)

**Alternativa**: Pode usar a **Emergent LLM Key** (chave universal já incluída no sistema)

---

## 🐛 Resolução de Problemas

### ❌ Bot não responde
- ✅ Verifique se a OpenAI API Key está configurada
- ✅ Confirme que há um prompt ATIVO
- ✅ Veja os logs: `tail -f /var/log/supervisor/backend.err.log`

### ❌ Webhook não recebe mensagens
- ✅ Verifique a URL do webhook na Evolution API
- ✅ Certifique-se que a Evolution API está acessível
- ✅ Confirme que o evento MESSAGES_UPSERT está ativo

### ❌ Mensagens não são enviadas
- ✅ Verifique Evolution API URL e Key nas Configurações
- ✅ Confirme o nome da instância correto
- ✅ Teste a conexão com: 
  ```bash
  curl -X GET 'https://sua-evolution-api.com/instance/connectionState/sua-instancia' \
    -H 'apikey: SUA-API-KEY'
  ```

### ❌ Conversa não aparece no dashboard
- ✅ Verifique se o webhook está recebendo dados
- ✅ Confirme que o MongoDB está rodando
- ✅ Recarregue a página "Conversas"

---

## 📊 Monitoramento

### Dashboard
- **Conversas Ativas**: Conversas abertas com bot respondendo
- **Transferidas**: Conversas aguardando atendimento humano
- **Mensagens Hoje**: Total de mensagens processadas hoje

### Conversas
- **Todas**: Ver todas as conversas
- **Ativas**: Apenas conversas com bot ativo
- **Transferidas**: Conversas aguardando atendimento humano

---

## 🚀 Próximos Passos

1. ✅ Configure webhook na Evolution API
2. ✅ Envie mensagem de teste
3. ✅ Veja aparecer em "Conversas"
4. ✅ Teste a resposta automática
5. ✅ Teste a transferência para humano
6. ✅ Configure prompts personalizados para seu negócio

---

## 📞 URLs Importantes

- **Dashboard**: http://localhost:3000
- **Página Webhook**: http://localhost:3000/webhook
- **API Backend**: Veja em `/app/frontend/.env`
- **Documentação Evolution API**: https://doc.evolution-api.com/

---

## 💡 Dicas

- **Personalize o prompt** para o tom da sua marca
- **Teste diferentes prompts** para ver qual converte melhor
- **Monitore conversas** regularmente para melhorar atendimento
- **Use keywords personalizadas** editando `/app/backend/bot_service.py`

---

**✅ Sistema está pronto para uso em produção!**

Qualquer dúvida, acesse a página "Webhook" no dashboard para ver exemplos de configuração.
