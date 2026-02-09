# 🔧 Troubleshooting - Mensagens não chegam no WhatsApp

## ❌ Problema: Webhook recebe mensagem, mas resposta não chega no WhatsApp

### Checklist de Diagnóstico

#### 1️⃣ Verificar Configurações

**Vá em "Configurações" e confirme:**

- [ ] ✅ OpenAI API Key está preenchida
- [ ] ✅ Evolution API URL está correta (ex: `https://evolution.seudominio.com`)
- [ ] ✅ Evolution API Key está correta
- [ ] ✅ Nome da Instância está correto (geralmente "default")
- [ ] ✅ Clicou em **"Salvar Configurações"** após preencher

⚠️ **IMPORTANTE**: Você DEVE clicar em "Salvar Configurações" para que o sistema inicialize a conexão com a Evolution API!

#### 2️⃣ Testar Conexão Evolution API

**Na página de Configurações:**

1. Role até "Evolution API (WhatsApp)"
2. Clique em **"Testar Conexão Evolution API"**
3. Verifique a mensagem:
   - ✅ "Conexão OK!" = Evolution está funcionando
   - ❌ Erro = Veja as soluções abaixo

#### 3️⃣ Verificar Formato do Endpoint Evolution API

A Evolution API tem formato específico para envio:

```
POST https://sua-evolution-api.com/message/sendText/{instance}
```

**Teste manual:**

```bash
curl -X POST 'https://sua-evolution-api.com/message/sendText/default' \
  -H 'apikey: SUA-API-KEY' \
  -H 'Content-Type: application/json' \
  -d '{
    "number": "5511999999999",
    "text": "Teste de mensagem"
  }'
```

Se este curl funcionar, o problema pode estar no código.

#### 4️⃣ Verificar Instância WhatsApp

**A instância precisa estar:**
- ✅ Conectada (QR Code escaneado)
- ✅ Online
- ✅ Nome correto nas configurações

**Para verificar:**

```bash
curl -X GET 'https://sua-evolution-api.com/instance/connectionState/default' \
  -H 'apikey: SUA-API-KEY'
```

Resposta esperada:
```json
{
  "state": "open"
}
```

#### 5️⃣ Verificar Logs do Backend

```bash
# Ver logs em tempo real
tail -f /var/log/supervisor/backend.err.log

# Procurar por erros de Evolution
tail -n 200 /var/log/supervisor/backend.err.log | grep -i "evolution\|error"
```

**O que procurar:**
- `✓ Message sent successfully` = Mensagem enviada!
- `✗ Failed to send message` = Erro no envio
- `Evolution service not initialized` = Configurações não foram salvas

---

## 🔍 Problemas Comuns e Soluções

### Problema 1: "Evolution service not initialized"

**Causa**: Configurações não foram salvas ou Evolution API não foi configurada

**Solução**:
1. Vá em "Configurações"
2. Preencha Evolution API URL, Key e Instância
3. Clique em **"Salvar Configurações"**
4. Aguarde a mensagem "Configurações salvas com sucesso!"
5. Teste enviando uma mensagem

### Problema 2: "Failed to send message"

**Causa**: URL incorreta, API Key inválida, ou instância desconectada

**Soluções**:

**A. Verificar URL**
```
✅ Correto: https://evolution.seudominio.com
❌ Errado: https://evolution.seudominio.com/
❌ Errado: https://evolution.seudominio.com/message
```

**B. Verificar API Key**
- Copie novamente do painel Evolution
- Verifique se não tem espaços extras
- Teste com curl (comando acima)

**C. Verificar Instância**
```bash
# Listar instâncias
curl -X GET 'https://sua-evolution-api.com/instance/fetchInstances' \
  -H 'apikey: SUA-API-KEY'
```

Pegue o nome exato da instância e use nas configurações.

**D. Reconectar WhatsApp**
- Vá no painel Evolution API
- Gere novo QR Code
- Escaneie novamente

### Problema 3: Mensagem salva no dashboard mas não envia

**Causa**: Evolution API configurada mas instância offline

**Solução**:
1. Verifique status da instância (comando acima)
2. Se `state: "close"`, reconecte o WhatsApp
3. Certifique-se que o WhatsApp Web não está aberto em outro lugar

### Problema 4: "Connection timeout"

**Causa**: Evolution API fora do ar ou firewall bloqueando

**Soluções**:
1. Teste a Evolution API diretamente no navegador
2. Verifique se a Evolution está rodando:
   ```bash
   # Se você hospeda a Evolution
   pm2 list
   docker ps  # se usa Docker
   ```
3. Verifique firewall/portas abertas

---

## 🧪 Como Testar Passo a Passo

### Teste 1: Verificar se Evolution API está acessível

```bash
curl -I https://sua-evolution-api.com
```

Deve retornar `200 OK` ou redirecionar.

### Teste 2: Verificar autenticação

```bash
curl -X GET 'https://sua-evolution-api.com/instance/fetchInstances' \
  -H 'apikey: SUA-API-KEY'
```

Deve retornar lista de instâncias, não erro 401/403.

### Teste 3: Enviar mensagem de teste

```bash
curl -X POST 'https://sua-evolution-api.com/message/sendText/default' \
  -H 'apikey: SUA-API-KEY' \
  -H 'Content-Type: application/json' \
  -d '{
    "number": "SEU-NUMERO-COM-DDI",
    "text": "Teste direto da API"
  }'
```

Se este teste funciona mas o sistema não envia, o problema está no código.

### Teste 4: Simular webhook completo

```bash
# Pegar URL do seu sistema
API_URL="https://seu-dominio.com"

# Enviar mensagem simulada
curl -X POST "$API_URL/api/webhook/meu-bot-whatsapp" \
  -H 'Content-Type: application/json' \
  -d '{
    "data": {
      "key": {
        "remoteJid": "SEU-NUMERO@s.whatsapp.net",
        "fromMe": false,
        "id": "TEST123"
      },
      "message": {
        "conversation": "Olá, teste!"
      },
      "messageTimestamp": 1234567890
    },
    "sender": "SEU-NUMERO@s.whatsapp.net",
    "pushName": "Teste"
  }'
```

Depois verifique:
1. Conversa apareceu em "Conversas"?
2. Bot respondeu?
3. Mensagem chegou no WhatsApp?
4. Logs mostram "✓ Message sent successfully"?

---

## 📋 Checklist Final

Antes de reportar problema, confirme:

- [ ] Salvei as configurações depois de preencher
- [ ] Testei conexão Evolution API (botão na página)
- [ ] Instância WhatsApp está conectada (QR Code escaneado)
- [ ] Evolution API está acessível (teste com curl)
- [ ] API Key está correta (sem espaços, cópia fresca)
- [ ] Nome da instância está correto (case-sensitive)
- [ ] WhatsApp Web não está aberto em outro dispositivo
- [ ] Verifiquei os logs do backend
- [ ] Testei envio manual via curl e funcionou

---

## 🆘 Ainda não funciona?

Se seguiu todos os passos acima e ainda não funciona:

1. **Compartilhe os logs:**
   ```bash
   tail -n 100 /var/log/supervisor/backend.err.log
   ```

2. **Compartilhe resposta do teste:**
   ```bash
   curl -X GET 'https://sua-evolution-api.com/instance/connectionState/sua-instancia' \
     -H 'apikey: SUA-API-KEY'
   ```

3. **Compartilhe configurações** (censure dados sensíveis):
   - Evolution API URL
   - Nome da instância
   - Se teste de conexão funciona

---

## 💡 Dicas de Sucesso

1. **Sempre salve** após alterar configurações
2. **Teste a conexão** antes de usar em produção
3. **Monitore os logs** durante os primeiros testes
4. **Use instância dedicada** para o bot (não use a mesma do WhatsApp pessoal)
5. **Mantenha WhatsApp conectado** (sem desconexões frequentes)
6. **Verifique limites** da Evolution API (rate limits)

---

## 🔐 Segurança

- **Nunca compartilhe** sua API Key publicamente
- **Use HTTPS** sempre (não HTTP)
- **Mude a API Key** se suspeitar de vazamento
- **Backup** das conversas regularmente

---

**Última atualização**: 2026-02-09

Se este guia ajudou, considere contribuir com melhorias! 🚀
