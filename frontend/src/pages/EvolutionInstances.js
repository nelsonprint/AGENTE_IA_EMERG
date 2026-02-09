import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { useAuth } from '../context/AuthContext';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Badge } from '../components/ui/badge';
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogTrigger, DialogFooter } from '../components/ui/dialog';
import { toast } from 'sonner';
import { Plus, Trash2, CheckCircle, Circle, RefreshCw } from 'lucide-react';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

const EvolutionInstances = () => {
  const { getAuthHeader } = useAuth();
  const [instances, setInstances] = useState([]);
  const [loading, setLoading] = useState(true);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [newInstance, setNewInstance] = useState({
    name: '',
    api_url: '',
    api_key: '',
    instance_name: 'default'
  });

  useEffect(() => {
    fetchInstances();
  }, []);

  const fetchInstances = async () => {
    try {
      const response = await axios.get(`${API}/evolution-instances`, getAuthHeader());
      setInstances(response.data);
    } catch (error) {
      console.error('Error fetching instances:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleAdd = async () => {
    try {
      await axios.post(`${API}/evolution-instances`, newInstance, getAuthHeader());
      toast.success('Instância adicionada com sucesso!');
      setDialogOpen(false);
      setNewInstance({ name: '', api_url: '', api_key: '', instance_name: 'default' });
      fetchInstances();
    } catch (error) {
      toast.error('Erro ao adicionar instância');
      console.error('Error adding instance:', error);
    }
  };

  const handleDelete = async (id) => {
    if (!window.confirm('Tem certeza que deseja excluir esta instância?')) return;

    try {
      await axios.delete(`${API}/evolution-instances/${id}`, getAuthHeader());
      toast.success('Instância excluída com sucesso!');
      fetchInstances();
    } catch (error) {
      toast.error('Erro ao excluir instância');
      console.error('Error deleting instance:', error);
    }
  };

  const handleSetDefault = async (id) => {
    try {
      await axios.post(`${API}/evolution-instances/${id}/set-default`, {}, getAuthHeader());
      toast.success('Instância padrão definida!');
      fetchInstances();
    } catch (error) {
      toast.error('Erro ao definir instância padrão');
      console.error('Error setting default:', error);
    }
  };

  const handleTestConnection = async (instance) => {
    try {
      const response = await axios.post(
        `${API}/evolution-instances/${instance.id}/test`,
        {},
        getAuthHeader()
      );
      if (response.data.status === 'success') {
        toast.success(`Conexão OK! Estado: ${response.data.connection.state}`);
      } else {
        toast.error('Erro na conexão');
      }
    } catch (error) {
      toast.error('Erro ao testar conexão');
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="text-muted-foreground">Carregando...</div>
      </div>
    );
  }

  return (
    <div className="p-6 md:p-8 space-y-6" data-testid="evolution-instances-page">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-4xl font-bold mb-2">Instâncias Evolution API</h1>
          <p className="text-muted-foreground">Gerencie múltiplas instâncias do WhatsApp</p>
        </div>
        <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
          <DialogTrigger asChild>
            <Button className="gap-2" data-testid="add-instance-button">
              <Plus className="w-4 h-4" />
              Nova Instância
            </Button>
          </DialogTrigger>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>Adicionar Nova Instância</DialogTitle>
              <DialogDescription>
                Configure uma nova instância Evolution API para WhatsApp
              </DialogDescription>
            </DialogHeader>
            <div className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="name">Nome de Identificação</Label>
                <Input
                  id="name"
                  placeholder="Ex: WhatsApp Vendas"
                  value={newInstance.name}
                  onChange={(e) => setNewInstance({ ...newInstance, name: e.target.value })}
                  data-testid="instance-name-input"
                />
                <p className="text-xs text-muted-foreground">Nome amigável para identificar</p>
              </div>
              <div className="space-y-2">
                <Label htmlFor="api-url">URL da Evolution API</Label>
                <Input
                  id="api-url"
                  placeholder="https://evolution.seudominio.com"
                  value={newInstance.api_url}
                  onChange={(e) => setNewInstance({ ...newInstance, api_url: e.target.value })}
                  data-testid="instance-url-input"
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="api-key">API Key</Label>
                <Input
                  id="api-key"
                  type="password"
                  placeholder="sua-api-key"
                  value={newInstance.api_key}
                  onChange={(e) => setNewInstance({ ...newInstance, api_key: e.target.value })}
                  data-testid="instance-key-input"
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="instance-name">Nome da Instância (Evolution)</Label>
                <Input
                  id="instance-name"
                  placeholder="default"
                  value={newInstance.instance_name}
                  onChange={(e) => setNewInstance({ ...newInstance, instance_name: e.target.value })}
                  data-testid="instance-evolution-name-input"
                />
                <p className="text-xs text-muted-foreground">
                  Nome da instância no painel Evolution API
                </p>
              </div>
            </div>
            <DialogFooter>
              <Button variant="outline" onClick={() => setDialogOpen(false)}>
                Cancelar
              </Button>
              <Button onClick={handleAdd} data-testid="save-instance-button">
                Adicionar
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      </div>

      {instances.length === 0 ? (
        <Card>
          <CardContent className="py-12 text-center">
            <p className="text-muted-foreground mb-4">
              Nenhuma instância cadastrada. Adicione sua primeira instância!
            </p>
            <Button onClick={() => setDialogOpen(true)} className="gap-2">
              <Plus className="w-4 h-4" />
              Adicionar Instância
            </Button>
          </CardContent>
        </Card>
      ) : (
        <div className="grid gap-4">
          {instances.map((instance) => (
            <Card
              key={instance.id}
              className="hover:border-zinc-700 transition-colors"
              data-testid={`instance-card-${instance.id}`}
            >
              <CardHeader>
                <div className="flex justify-between items-start">
                  <div className="flex-1">
                    <div className="flex items-center gap-2 mb-2">
                      <CardTitle>{instance.name}</CardTitle>
                      {instance.is_default && (
                        <Badge className="bg-primary/20 text-primary border-primary/30">
                          <CheckCircle className="w-3 h-3 mr-1" />
                          Padrão
                        </Badge>
                      )}
                    </div>
                    <CardDescription className="space-y-1">
                      <div className="flex items-center gap-2">
                        <span className="text-xs font-mono">Instância:</span>
                        <code className="text-xs bg-secondary px-2 py-1 rounded">
                          {instance.instance_name}
                        </code>
                      </div>
                      <div className="flex items-center gap-2">
                        <span className="text-xs font-mono">URL:</span>
                        <code className="text-xs text-muted-foreground">
                          {instance.api_url}
                        </code>
                      </div>
                    </CardDescription>
                  </div>
                  <div className="flex gap-2">
                    {!instance.is_default && (
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => handleSetDefault(instance.id)}
                        data-testid={`set-default-${instance.id}`}
                      >
                        <CheckCircle className="w-4 h-4" />
                      </Button>
                    )}
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => handleTestConnection(instance)}
                      data-testid={`test-${instance.id}`}
                    >
                      <RefreshCw className="w-4 h-4" />
                    </Button>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => handleDelete(instance.id)}
                      className="text-destructive hover:bg-destructive/10"
                      data-testid={`delete-${instance.id}`}
                    >
                      <Trash2 className="w-4 h-4" />
                    </Button>
                  </div>
                </div>
              </CardHeader>
            </Card>
          ))}
        </div>
      )}

      <Card className="bg-blue-500/5 border-blue-500/20">
        <CardContent className="pt-6">
          <div className="flex gap-2">
            <div className="text-blue-400">💡</div>
            <div className="flex-1">
              <p className="text-sm font-medium text-blue-400 mb-1">Dica</p>
              <p className="text-xs text-muted-foreground">
                A instância marcada como "Padrão" será usada para enviar todas as mensagens.
                Você pode ter várias instâncias cadastradas e alternar entre elas facilmente.
              </p>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default EvolutionInstances;
