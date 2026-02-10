import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { useAuth } from '../context/AuthContext';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/ui/card';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Button } from '../components/ui/button';
import { toast } from 'sonner';
import { Eye, EyeOff, Save, Plus, X } from 'lucide-react';
import { Badge } from '../components/ui/badge';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

const Settings = () => {
  const { getAuthHeader } = useAuth();
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [testing, setTesting] = useState(false);
  const [showKeys, setShowKeys] = useState({});
  const [settings, setSettings] = useState({
    openai_api_key: '',
    evolution_api_url: '',
    evolution_api_key: '',
    evolution_instance: 'default',
    supabase_url: '',
    supabase_key: '',
    redis_url: '',
    redis_password: '',
    notification_whatsapp: '',
    transfer_keywords: []
  });
  const [newKeyword, setNewKeyword] = useState('');

  useEffect(() => {
    fetchSettings();
  }, []);

  const fetchSettings = async () => {
    try {
      const response = await axios.get(`${API}/settings`, getAuthHeader());
      setSettings(response.data);
    } catch (error) {
      console.error('Error fetching settings:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleSave = async () => {
    setSaving(true);
    try {
      await axios.put(`${API}/settings`, settings, getAuthHeader());
      toast.success('Configurações salvas com sucesso!');
    } catch (error) {
      toast.error('Erro ao salvar configurações');
      console.error('Error saving settings:', error);
    } finally {
      setSaving(false);
    }
  };

  const handleTestEvolution = async () => {
    setTesting(true);
    try {
      const response = await axios.get(`${API}/evolution/test`, getAuthHeader());
      if (response.data.status === 'success') {
        toast.success(`Conexão OK! Instância: ${response.data.instance}`);
      } else {
        toast.error(response.data.message || 'Erro ao testar conexão');
      }
    } catch (error) {
      toast.error('Erro ao testar Evolution API');
      console.error('Error testing evolution:', error);
    } finally {
      setTesting(false);
    }
  };

  const toggleShowKey = (field) => {
    setShowKeys(prev => ({ ...prev, [field]: !prev[field] }));
  };

  const maskValue = (value) => {
    if (!value) return '';
    return '•'.repeat(Math.min(value.length, 20));
  };

  const SettingField = ({ label, field, placeholder, description }) => (
    <div className="space-y-2">
      <Label htmlFor={field}>{label}</Label>
      <div className="relative">
        <Input
          id={field}
          type={showKeys[field] ? 'text' : 'password'}
          placeholder={placeholder}
          value={showKeys[field] ? settings[field] : maskValue(settings[field])}
          onChange={(e) => setSettings({ ...settings, [field]: e.target.value })}
          className="pr-10 font-mono text-sm"
          data-testid={`settings-input-${field}`}
        />
        <Button
          type="button"
          variant="ghost"
          size="sm"
          className="absolute right-1 top-1/2 -translate-y-1/2"
          onClick={() => toggleShowKey(field)}
          data-testid={`toggle-${field}`}
        >
          {showKeys[field] ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
        </Button>
      </div>
      {description && <p className="text-xs text-muted-foreground">{description}</p>}
    </div>
  );

  if (loading) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="text-muted-foreground">Carregando...</div>
      </div>
    );
  }

  return (
    <div className="p-6 md:p-8 space-y-6 max-w-4xl" data-testid="settings-page">
      <div>
        <h1 className="text-4xl font-bold mb-2">Configurações</h1>
        <p className="text-muted-foreground">Configure as chaves de API e credenciais</p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>OpenAI API</CardTitle>
          <CardDescription>
            Chave de API para o modelo GPT-4o-mini
          </CardDescription>
        </CardHeader>
        <CardContent>
          <SettingField
            label="OpenAI API Key"
            field="openai_api_key"
            placeholder="sk-..."
            description="Obtenha sua chave em https://platform.openai.com/api-keys"
          />
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <span>🔔</span> Notificações de Transferência
          </CardTitle>
          <CardDescription>
            Receba uma mensagem no seu WhatsApp quando um cliente solicitar atendimento humano
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-2">
            <Label htmlFor="notification_whatsapp">Seu WhatsApp para Notificações</Label>
            <Input
              id="notification_whatsapp"
              type="text"
              placeholder="5511999999999"
              value={settings.notification_whatsapp || ''}
              onChange={(e) => setSettings({ ...settings, notification_whatsapp: e.target.value })}
              className="font-mono text-sm"
              data-testid="settings-input-notification_whatsapp"
            />
            <p className="text-xs text-muted-foreground">
              Digite seu número com código do país (ex: 5511999999999). Você receberá notificações quando um cliente pedir para falar com o dono, gerente, comercial, etc.
            </p>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Evolution API (WhatsApp)</CardTitle>
          <CardDescription>
            Credenciais para enviar e receber mensagens do WhatsApp
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <SettingField
            label="URL da API"
            field="evolution_api_url"
            placeholder="https://sua-evolution-api.com"
          />
          <SettingField
            label="API Key"
            field="evolution_api_key"
            placeholder="sua-chave-api"
          />
          <div className="space-y-2">
            <Label htmlFor="evolution-instance">Nome da Instância</Label>
            <Input
              id="evolution-instance"
              type="text"
              placeholder="default"
              value={settings.evolution_instance}
              onChange={(e) => setSettings({ ...settings, evolution_instance: e.target.value })}
              className="font-mono text-sm"
              data-testid="settings-input-evolution_instance"
            />
            <p className="text-xs text-muted-foreground">
              Nome da sua instância na Evolution API (geralmente "default" ou nome personalizado)
            </p>
          </div>
          <Button
            variant="outline"
            onClick={handleTestEvolution}
            disabled={testing || !settings.evolution_api_url}
            className="w-full"
            data-testid="test-evolution-button"
          >
            {testing ? 'Testando...' : 'Testar Conexão Evolution API'}
          </Button>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Supabase</CardTitle>
          <CardDescription>
            Banco de dados para armazenar usuários e mensagens
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <SettingField
            label="Supabase URL"
            field="supabase_url"
            placeholder="https://seu-projeto.supabase.co"
          />
          <SettingField
            label="Supabase Key"
            field="supabase_key"
            placeholder="sua-chave-anon"
          />
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Redis</CardTitle>
          <CardDescription>
            Cache de memória de conversação (já configurado automaticamente)
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="bg-green-500/10 border border-green-500/20 rounded-lg p-3 mb-4">
            <p className="text-xs text-green-400">
              ✓ <strong>Redis local ativo!</strong> URL padrão: redis://127.0.0.1:6379
            </p>
          </div>
          <SettingField
            label="Redis URL"
            field="redis_url"
            placeholder="redis://127.0.0.1:6379"
          />
          <SettingField
            label="Redis Password (opcional)"
            field="redis_password"
            placeholder="deixe vazio para Redis local"
          />
        </CardContent>
      </Card>

      <div className="flex justify-end">
        <Button 
          onClick={handleSave} 
          disabled={saving} 
          className="gap-2"
          data-testid="save-settings-button"
        >
          <Save className="w-4 h-4" />
          {saving ? 'Salvando...' : 'Salvar Configurações'}
        </Button>
      </div>
    </div>
  );
};

export default Settings;