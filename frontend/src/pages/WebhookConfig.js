import React, { useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/ui/card';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Button } from '../components/ui/button';
import { Badge } from '../components/ui/badge';
import { Copy, Check, Webhook, Code } from 'lucide-react';
import { toast } from 'sonner';

const WebhookConfig = () => {
  const [webhookId, setWebhookId] = useState('meu-bot-whatsapp');
  const [copied, setCopied] = useState(false);

  const backendUrl = process.env.REACT_APP_BACKEND_URL || 'https://seu-dominio.com';
  const webhookUrl = `${backendUrl}/api/webhook/${webhookId}`;

  const handleCopy = (text) => {
    navigator.clipboard.writeText(text);
    setCopied(true);
    toast.success('Copiado para a área de transferência!');
    setTimeout(() => setCopied(false), 2000);
  };

  const evolutionApiConfig = {
    webhook: {
      url: webhookUrl,
      webhook_by_events: false,
      webhook_base64: false,
      events: [
        "MESSAGES_UPSERT",
        "MESSAGES_UPDATE",
        "MESSAGES_DELETE",
        "SEND_MESSAGE"
      ]
    }
  };

  const curlExample = `curl -X POST '${webhookUrl}' \\
  -H 'Content-Type: application/json' \\
  -d '{
    "data": {
      "key": {
        "remoteJid": "5511999999999@s.whatsapp.net",
        "fromMe": false,
        "id": "3EB0123456789ABCDEF"
      },
      "message": {
        "conversation": "Olá, preciso de ajuda!"
      },
      "messageTimestamp": 1234567890
    },
    "sender": "5511999999999@s.whatsapp.net",
    "pushName": "João Silva"
  }'`;

  return (
    <div className="p-6 md:p-8 space-y-6" data-testid="webhook-config-page">
      <div>
        <h1 className="text-4xl font-bold mb-2">Configuração do Webhook</h1>
        <p className="text-muted-foreground">
          Configure o webhook na Evolution API para receber mensagens
        </p>
      </div>

      {/* Webhook URL Generator */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Webhook className="w-5 h-5" />
            URL do Webhook
          </CardTitle>
          <CardDescription>
            Personalize o ID do webhook e copie a URL para configurar na Evolution API
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="webhook-id">ID do Webhook (personalizável)</Label>
            <Input
              id="webhook-id"
              value={webhookId}
              onChange={(e) => setWebhookId(e.target.value.replace(/\s/g, '-'))}
              placeholder="meu-bot-whatsapp"
              data-testid="webhook-id-input"
            />
            <p className="text-xs text-muted-foreground">
              Use apenas letras, números e hífens
            </p>
          </div>

          <div className="space-y-2">
            <Label>Sua URL do Webhook</Label>
            <div className="flex gap-2">
              <div className="flex-1 p-3 bg-secondary rounded-md font-mono text-sm break-all">
                {webhookUrl}
              </div>
              <Button
                variant="outline"
                size="icon"
                onClick={() => handleCopy(webhookUrl)}
                data-testid="copy-webhook-url"
              >
                {copied ? <Check className="w-4 h-4 text-primary" /> : <Copy className="w-4 h-4" />}
              </Button>
            </div>
          </div>

          <div className="bg-amber-500/10 border border-amber-500/20 rounded-lg p-4">
            <div className="flex gap-2">
              <div className="text-amber-500">⚠️</div>
              <div className="flex-1">
                <p className="text-sm font-medium text-amber-500">Importante</p>
                <p className="text-xs text-muted-foreground mt-1">
                  Esta URL precisa ser configurada na sua instância da Evolution API para que as mensagens sejam enviadas para este sistema.
                </p>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Evolution API Configuration */}
      <Card>
        <CardHeader>
          <CardTitle>Passo a Passo - Configurar na Evolution API</CardTitle>
          <CardDescription>
            Como configurar o webhook na sua instância Evolution API
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-3">
            <div className="flex gap-3">
              <Badge className="bg-primary/20 text-primary shrink-0">1</Badge>
              <div>
                <p className="font-medium">Acesse o painel da Evolution API</p>
                <p className="text-sm text-muted-foreground">
                  Entre no seu painel Evolution API (exemplo: https://evolution.seudominio.com)
                </p>
              </div>
            </div>

            <div className="flex gap-3">
              <Badge className="bg-primary/20 text-primary shrink-0">2</Badge>
              <div>
                <p className="font-medium">Selecione sua instância</p>
                <p className="text-sm text-muted-foreground">
                  Escolha a instância do WhatsApp que você quer conectar ao bot
                </p>
              </div>
            </div>

            <div className="flex gap-3">
              <Badge className="bg-primary/20 text-primary shrink-0">3</Badge>
              <div>
                <p className="font-medium">Configure o Webhook</p>
                <p className="text-sm text-muted-foreground mb-2">
                  Vá em "Webhook" e adicione a URL gerada acima
                </p>
                <div className="bg-secondary p-3 rounded-md font-mono text-xs">
                  {webhookUrl}
                </div>
              </div>
            </div>

            <div className="flex gap-3">
              <Badge className="bg-primary/20 text-primary shrink-0">4</Badge>
              <div>
                <p className="font-medium">Ative os eventos</p>
                <p className="text-sm text-muted-foreground">
                  Marque: MESSAGES_UPSERT (principal para receber mensagens)
                </p>
              </div>
            </div>

            <div className="flex gap-3">
              <Badge className="bg-primary/20 text-primary shrink-0">5</Badge>
              <div>
                <p className="font-medium">Salve e teste</p>
                <p className="text-sm text-muted-foreground">
                  Envie uma mensagem de teste pelo WhatsApp e veja aparecer em "Conversas"
                </p>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* JSON Configuration */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Code className="w-5 h-5" />
            Configuração JSON (API)
          </CardTitle>
          <CardDescription>
            Se você usa a API da Evolution, use esta configuração
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-2">
            <div className="flex justify-between items-center">
              <Label>Payload JSON</Label>
              <Button
                variant="outline"
                size="sm"
                onClick={() => handleCopy(JSON.stringify(evolutionApiConfig, null, 2))}
              >
                <Copy className="w-3 h-3 mr-2" />
                Copiar
              </Button>
            </div>
            <pre className="bg-secondary p-4 rounded-md overflow-x-auto text-xs font-mono">
              {JSON.stringify(evolutionApiConfig, null, 2)}
            </pre>
          </div>

          <div className="text-sm text-muted-foreground">
            <p className="font-medium mb-2">Endpoint da Evolution API:</p>
            <code className="bg-secondary px-2 py-1 rounded">
              POST https://sua-evolution-api.com/webhook/set/sua-instancia
            </code>
          </div>
        </CardContent>
      </Card>

      {/* Test Webhook */}
      <Card>
        <CardHeader>
          <CardTitle>Testar Webhook (cURL)</CardTitle>
          <CardDescription>
            Teste se o webhook está funcionando enviando uma mensagem simulada
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-2">
            <div className="flex justify-between items-center">
              <Label>Comando cURL</Label>
              <Button
                variant="outline"
                size="sm"
                onClick={() => handleCopy(curlExample)}
              >
                <Copy className="w-3 h-3 mr-2" />
                Copiar
              </Button>
            </div>
            <pre className="bg-secondary p-4 rounded-md overflow-x-auto text-xs font-mono">
              {curlExample}
            </pre>
          </div>

          <div className="bg-blue-500/10 border border-blue-500/20 rounded-lg p-4">
            <p className="text-sm text-blue-400">
              💡 <strong>Dica:</strong> Execute este comando no terminal para simular uma mensagem recebida. 
              A conversa deve aparecer em "Conversas" no menu.
            </p>
          </div>
        </CardContent>
      </Card>

      {/* What Happens */}
      <Card>
        <CardHeader>
          <CardTitle>Como Funciona?</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-3 text-sm">
            <div className="flex items-start gap-3">
              <div className="w-8 h-8 rounded-full bg-primary/20 flex items-center justify-center shrink-0 text-primary font-bold">
                1
              </div>
              <div>
                <p className="font-medium">Usuário envia mensagem no WhatsApp</p>
                <p className="text-muted-foreground">Cliente envia "Olá, preciso de ajuda"</p>
              </div>
            </div>

            <div className="flex items-start gap-3">
              <div className="w-8 h-8 rounded-full bg-primary/20 flex items-center justify-center shrink-0 text-primary font-bold">
                2
              </div>
              <div>
                <p className="font-medium">Evolution API recebe e envia para webhook</p>
                <p className="text-muted-foreground">A Evolution chama: {webhookUrl}</p>
              </div>
            </div>

            <div className="flex items-start gap-3">
              <div className="w-8 h-8 rounded-full bg-primary/20 flex items-center justify-center shrink-0 text-primary font-bold">
                3
              </div>
              <div>
                <p className="font-medium">Sistema processa com IA</p>
                <p className="text-muted-foreground">
                  Usa OpenAI GPT-4o-mini com seu prompt configurado
                </p>
              </div>
            </div>

            <div className="flex items-start gap-3">
              <div className="w-8 h-8 rounded-full bg-primary/20 flex items-center justify-center shrink-0 text-primary font-bold">
                4
              </div>
              <div>
                <p className="font-medium">Resposta enviada de volta</p>
                <p className="text-muted-foreground">
                  Bot responde automaticamente no WhatsApp (via Evolution API)
                </p>
              </div>
            </div>

            <div className="flex items-start gap-3">
              <div className="w-8 h-8 rounded-full bg-primary/20 flex items-center justify-center shrink-0 text-primary font-bold">
                5
              </div>
              <div>
                <p className="font-medium">Histórico salvo</p>
                <p className="text-muted-foreground">
                  Toda conversa aparece em "Conversas" para você monitorar
                </p>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default WebhookConfig;
