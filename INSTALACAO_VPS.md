# Guia de Instalação - WhatsApp Bot AI

## Requisitos do Servidor VPS

- **Sistema Operacional:** Ubuntu 20.04+ ou Debian 11+
- **RAM:** Mínimo 2GB (recomendado 4GB)
- **CPU:** 2 vCPUs
- **Disco:** 20GB SSD
- **Portas abertas:** 80, 443, 8001, 3000

---

## Passo 1: Atualizar o Sistema

```bash
sudo apt update && sudo apt upgrade -y
```

---

## Passo 2: Instalar Dependências

```bash
# Instalar Node.js 18+
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt install -y nodejs

# Instalar Python 3.10+
sudo apt install -y python3 python3-pip python3-venv

# Instalar MongoDB
curl -fsSL https://pgp.mongodb.com/server-7.0.asc | sudo gpg -o /usr/share/keyrings/mongodb-server-7.0.gpg --dearmor
echo "deb [ signed-by=/usr/share/keyrings/mongodb-server-7.0.gpg ] https://repo.mongodb.org/apt/ubuntu jammy/mongodb-org/7.0 multiverse" | sudo tee /etc/apt/sources.list.d/mongodb-org-7.0.list
sudo apt update
sudo apt install -y mongodb-org

# Iniciar MongoDB
sudo systemctl start mongod
sudo systemctl enable mongod

# Instalar Redis (opcional - para cache de conversas)
sudo apt install -y redis-server
sudo systemctl start redis-server
sudo systemctl enable redis-server

# Instalar Nginx (proxy reverso)
sudo apt install -y nginx

# Instalar Git
sudo apt install -y git

# Instalar Supervisor (gerenciador de processos)
sudo apt install -y supervisor

# Instalar Yarn
npm install -g yarn
```

---

## Passo 3: Criar Usuário para Aplicação

```bash
sudo useradd -m -s /bin/bash whatsappbot
sudo usermod -aG sudo whatsappbot
```

---

## Passo 4: Clonar/Copiar os Arquivos do Projeto

```bash
# Criar diretório da aplicação
sudo mkdir -p /opt/whatsappbot
sudo chown whatsappbot:whatsappbot /opt/whatsappbot

# Mudar para o usuário da aplicação
sudo su - whatsappbot

# Copiar os arquivos do projeto para /opt/whatsappbot
# (use SCP, SFTP ou Git para transferir os arquivos)
cd /opt/whatsappbot
```

A estrutura deve ficar assim:
```
/opt/whatsappbot/
├── backend/
│   ├── server.py
│   ├── bot_service.py
│   ├── requirements.txt
│   └── .env
├── frontend/
│   ├── src/
│   ├── package.json
│   └── .env
```

---

## Passo 5: Configurar o Backend

```bash
cd /opt/whatsappbot/backend

# Criar ambiente virtual Python
python3 -m venv venv
source venv/bin/activate

# Instalar dependências
pip install --upgrade pip
pip install -r requirements.txt
pip install emergentintegrations --extra-index-url https://d33sy5i8bnduwe.cloudfront.net/simple/

# Criar arquivo .env
nano .env
```

**Conteúdo do `/opt/whatsappbot/backend/.env`:**
```
MONGO_URL=mongodb://127.0.0.1:27017
DB_NAME=whatsappbot
```

---

## Passo 6: Configurar o Frontend

```bash
cd /opt/whatsappbot/frontend

# Instalar dependências
yarn install

# Criar arquivo .env
nano .env
```

**Conteúdo do `/opt/whatsappbot/frontend/.env`:**
```
REACT_APP_BACKEND_URL=https://gpsdonegocio.com
```

```bash
# Build do frontend para produção
yarn build
```

---

## Passo 7: Configurar Supervisor

```bash
sudo nano /etc/supervisor/conf.d/whatsappbot.conf
```

**Conteúdo:**
```ini
[program:backend]
directory=/opt/whatsappbot/backend
command=/opt/whatsappbot/backend/venv/bin/uvicorn server:app --host 0.0.0.0 --port 8001
user=whatsappbot
autostart=true
autorestart=true
stderr_logfile=/var/log/supervisor/backend.err.log
stdout_logfile=/var/log/supervisor/backend.out.log
environment=PATH="/opt/whatsappbot/backend/venv/bin"

[program:frontend]
directory=/opt/whatsappbot/frontend
command=/usr/bin/npx serve -s build -l 3000
user=whatsappbot
autostart=true
autorestart=true
stderr_logfile=/var/log/supervisor/frontend.err.log
stdout_logfile=/var/log/supervisor/frontend.out.log
```

```bash
# Recarregar supervisor
sudo supervisorctl reread
sudo supervisorctl update
sudo supervisorctl start all

# Verificar status
sudo supervisorctl status
```

---

## Passo 8: Configurar Nginx (Proxy Reverso + SSL)

```bash
sudo nano /etc/nginx/sites-available/whatsappbot
```

**Conteúdo:**
```nginx
server {
    listen 80;
    server_name gpsdonegocio.com www.gpsdonegocio.com;
    
    # Redirecionar para HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name gpsdonegocio.com www.gpsdonegocio.com;

    # SSL será configurado pelo Certbot
    # ssl_certificate /etc/letsencrypt/live/gpsdonegocio.com/fullchain.pem;
    # ssl_certificate_key /etc/letsencrypt/live/gpsdonegocio.com/privkey.pem;

    # Frontend
    location / {
        proxy_pass http://127.0.0.1:3000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
    }

    # Backend API
    location /api {
        proxy_pass http://127.0.0.1:8001;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
        
        # Timeout para webhooks
        proxy_read_timeout 120s;
        proxy_connect_timeout 120s;
        proxy_send_timeout 120s;
    }
}
```

```bash
# Ativar o site
sudo ln -s /etc/nginx/sites-available/whatsappbot /etc/nginx/sites-enabled/

# Remover site default
sudo rm /etc/nginx/sites-enabled/default

# Testar configuração
sudo nginx -t

# Reiniciar Nginx
sudo systemctl restart nginx
```

---

## Passo 9: Configurar SSL com Let's Encrypt

```bash
# Instalar Certbot
sudo apt install -y certbot python3-certbot-nginx

# Obter certificado SSL
sudo certbot --nginx -d gpsdonegocio.com -d www.gpsdonegocio.com

# Renovação automática (já configurada pelo certbot)
sudo systemctl enable certbot.timer
```

---

## Passo 10: Configurar Firewall

```bash
sudo ufw allow 22/tcp    # SSH
sudo ufw allow 80/tcp    # HTTP
sudo ufw allow 443/tcp   # HTTPS
sudo ufw enable
```

---

## Passo 11: Verificar se Tudo Está Funcionando

```bash
# Verificar serviços
sudo supervisorctl status
sudo systemctl status nginx
sudo systemctl status mongod

# Testar backend
curl http://localhost:8001/api/health

# Testar frontend
curl http://localhost:3000
```

---

## Passo 12: Acessar o Sistema

1. Acesse: `https://gpsdonegocio.com`
2. Faça login com: `admin` / `admin123`
3. Configure em **Configurações**:
   - OpenAI API Key
   - Evolution API URL e Key
   - Seu WhatsApp para notificações
4. Configure o **Prompt** da IA
5. Copie o **Webhook URL** e configure na Evolution API

---

## Comandos Úteis

```bash
# Ver logs do backend
tail -f /var/log/supervisor/backend.err.log

# Ver logs do frontend
tail -f /var/log/supervisor/frontend.err.log

# Reiniciar serviços
sudo supervisorctl restart backend
sudo supervisorctl restart frontend

# Reiniciar tudo
sudo supervisorctl restart all

# Ver status
sudo supervisorctl status
```

---

## Backup do Banco de Dados

```bash
# Fazer backup
mongodump --db whatsappbot --out /backup/mongodb/$(date +%Y%m%d)

# Restaurar backup
mongorestore --db whatsappbot /backup/mongodb/20240101/whatsappbot
```

---

## Solução de Problemas

### Backend não inicia
```bash
cd /opt/whatsappbot/backend
source venv/bin/activate
python server.py
# Veja o erro específico
```

### Frontend não inicia
```bash
cd /opt/whatsappbot/frontend
yarn start
# Veja o erro específico
```

### Webhook não recebe mensagens
1. Verifique se o Nginx está rodando: `sudo systemctl status nginx`
2. Verifique se a URL está correta na Evolution API
3. Teste com curl: `curl -X POST https://gpsdonegocio.com/api/webhook/meu-bot-whatsapp`

### Erro de conexão com MongoDB
```bash
sudo systemctl status mongod
sudo systemctl start mongod
```

---

## Manutenção

### Atualizar o sistema
```bash
cd /opt/whatsappbot
git pull  # se usando Git

# Atualizar backend
cd backend
source venv/bin/activate
pip install -r requirements.txt
sudo supervisorctl restart backend

# Atualizar frontend
cd ../frontend
yarn install
yarn build
sudo supervisorctl restart frontend
```

---

## Contato e Suporte

- WhatsApp: https://wa.link/te6a83
- Atendimento: 9h às 23h todos os dias
