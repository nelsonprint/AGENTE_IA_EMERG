import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { useAuth } from '../context/AuthContext';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Textarea } from '../components/ui/textarea';
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogTrigger, DialogFooter } from '../components/ui/dialog';
import { Badge } from '../components/ui/badge';
import { toast } from 'sonner';
import { Plus, Edit, Trash2, CheckCircle, Circle } from 'lucide-react';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

const Prompts = () => {
  const { getAuthHeader } = useAuth();
  const [prompts, setPrompts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [editingPrompt, setEditingPrompt] = useState(null);
  const [formData, setFormData] = useState({
    name: '',
    system_prompt: '',
    is_active: false
  });

  useEffect(() => {
    fetchPrompts();
  }, []);

  const fetchPrompts = async () => {
    try {
      const response = await axios.get(`${API}/prompts`, getAuthHeader());
      setPrompts(response.data);
    } catch (error) {
      console.error('Error fetching prompts:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleOpenDialog = (prompt = null) => {
    if (prompt) {
      setEditingPrompt(prompt);
      setFormData({
        name: prompt.name,
        system_prompt: prompt.system_prompt,
        is_active: prompt.is_active
      });
    } else {
      setEditingPrompt(null);
      setFormData({ name: '', system_prompt: '', is_active: false });
    }
    setDialogOpen(true);
  };

  const handleSave = async () => {
    try {
      if (editingPrompt) {
        await axios.put(`${API}/prompts/${editingPrompt.id}`, formData, getAuthHeader());
        toast.success('Prompt atualizado com sucesso!');
      } else {
        await axios.post(`${API}/prompts`, formData, getAuthHeader());
        toast.success('Prompt criado com sucesso!');
      }
      setDialogOpen(false);
      fetchPrompts();
    } catch (error) {
      toast.error('Erro ao salvar prompt');
      console.error('Error saving prompt:', error);
    }
  };

  const handleDelete = async (promptId) => {
    if (!window.confirm('Tem certeza que deseja excluir este prompt?')) return;
    
    try {
      await axios.delete(`${API}/prompts/${promptId}`, getAuthHeader());
      toast.success('Prompt excluído com sucesso!');
      fetchPrompts();
    } catch (error) {
      toast.error('Erro ao excluir prompt');
      console.error('Error deleting prompt:', error);
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
    <div className="p-6 md:p-8 space-y-6" data-testid="prompts-page">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-4xl font-bold mb-2">Prompts do Bot</h1>
          <p className="text-muted-foreground">Configure o comportamento do assistente</p>
        </div>
        <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
          <DialogTrigger asChild>
            <Button onClick={() => handleOpenDialog()} className="gap-2" data-testid="create-prompt-button">
              <Plus className="w-4 h-4" />
              Novo Prompt
            </Button>
          </DialogTrigger>
          <DialogContent className="max-w-2xl">
            <DialogHeader>
              <DialogTitle>{editingPrompt ? 'Editar Prompt' : 'Novo Prompt'}</DialogTitle>
              <DialogDescription>
                Configure as instruções do sistema para o assistente de IA
              </DialogDescription>
            </DialogHeader>
            <div className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="prompt-name">Nome</Label>
                <Input
                  id="prompt-name"
                  placeholder="Ex: Atendimento Amigável"
                  value={formData.name}
                  onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                  data-testid="prompt-name-input"
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="system-prompt">Prompt do Sistema</Label>
                <Textarea
                  id="system-prompt"
                  placeholder="Você é um assistente virtual..."
                  value={formData.system_prompt}
                  onChange={(e) => setFormData({ ...formData, system_prompt: e.target.value })}
                  rows={10}
                  className="font-mono text-sm"
                  data-testid="prompt-content-input"
                />
              </div>
              <div className="flex items-center gap-2">
                <input
                  type="checkbox"
                  id="is-active"
                  checked={formData.is_active}
                  onChange={(e) => setFormData({ ...formData, is_active: e.target.checked })}
                  className="w-4 h-4"
                  data-testid="prompt-active-checkbox"
                />
                <Label htmlFor="is-active">Ativar este prompt</Label>
              </div>
            </div>
            <DialogFooter>
              <Button variant="outline" onClick={() => setDialogOpen(false)} data-testid="cancel-prompt-button">
                Cancelar
              </Button>
              <Button onClick={handleSave} data-testid="save-prompt-button">
                {editingPrompt ? 'Atualizar' : 'Criar'}
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      </div>

      {prompts.length === 0 ? (
        <Card>
          <CardContent className="py-12 text-center">
            <p className="text-muted-foreground">Nenhum prompt cadastrado. Crie seu primeiro prompt!</p>
          </CardContent>
        </Card>
      ) : (
        <div className="grid gap-4">
          {prompts.map((prompt) => (
            <Card key={prompt.id} className="hover:border-zinc-700 transition-colors" data-testid={`prompt-card-${prompt.id}`}>
              <CardHeader>
                <div className="flex justify-between items-start">
                  <div className="flex-1">
                    <div className="flex items-center gap-2 mb-2">
                      <CardTitle>{prompt.name}</CardTitle>
                      {prompt.is_active ? (
                        <Badge className="bg-primary/20 text-primary border-primary/30" data-testid={`prompt-active-badge-${prompt.id}`}>
                          <CheckCircle className="w-3 h-3 mr-1" />
                          Ativo
                        </Badge>
                      ) : (
                        <Badge variant="outline" className="text-muted-foreground">
                          <Circle className="w-3 h-3 mr-1" />
                          Inativo
                        </Badge>
                      )}
                    </div>
                    <CardDescription className="font-mono text-xs">
                      {prompt.system_prompt.substring(0, 150)}...
                    </CardDescription>
                  </div>
                  <div className="flex gap-2">
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => handleOpenDialog(prompt)}
                      data-testid={`edit-prompt-button-${prompt.id}`}
                    >
                      <Edit className="w-4 h-4" />
                    </Button>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => handleDelete(prompt.id)}
                      className="text-destructive hover:bg-destructive/10"
                      data-testid={`delete-prompt-button-${prompt.id}`}
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
    </div>
  );
};

export default Prompts;