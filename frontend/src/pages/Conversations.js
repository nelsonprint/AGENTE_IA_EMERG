import React, { useState, useEffect, useRef } from 'react';
import axios from 'axios';
import { useAuth } from '../context/AuthContext';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Badge } from '../components/ui/badge';
import { ScrollArea } from '../components/ui/scroll-area';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../components/ui/tabs';
import { toast } from 'sonner';
import { MessageSquare, User, Bot, ArrowRight, X, Send } from 'lucide-react';
import { Input } from '../components/ui/input';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

const Conversations = () => {
  const { getAuthHeader } = useAuth();
  const [conversations, setConversations] = useState([]);
  const [selectedConversation, setSelectedConversation] = useState(null);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState('all');
  const [message, setMessage] = useState('');
  const messagesEndRef = useRef(null);
  const selectedConversationRef = useRef(null);

  // Keep track of selected conversation ID to prevent losing focus
  const selectedIdRef = useRef(null);

  useEffect(() => {
    fetchConversations();
    const interval = setInterval(fetchConversations, 10000); // Refresh every 10s
    return () => clearInterval(interval);
  }, [filter]);

  // Scroll to bottom when messages change
  useEffect(() => {
    scrollToBottom();
  }, [selectedConversation?.messages]);

  const scrollToBottom = () => {
    if (messagesEndRef.current) {
      messagesEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  };

  const fetchConversations = async () => {
    try {
      const url = filter === 'all' ? `${API}/conversations` : `${API}/conversations?status=${filter}`;
      const response = await axios.get(url, getAuthHeader());
      
      // Sort conversations by last message time (newest first)
      const sortedConversations = response.data.sort((a, b) => {
        const timeA = new Date(a.last_message_at || a.started_at);
        const timeB = new Date(b.last_message_at || b.started_at);
        return timeB - timeA;
      });
      
      setConversations(sortedConversations);
      
      // Update selected conversation without losing focus
      // Only update if we have a selected conversation
      if (selectedIdRef.current) {
        const updated = sortedConversations.find(c => c.id === selectedIdRef.current);
        if (updated) {
          setSelectedConversation(updated);
        }
      }
    } catch (error) {
      console.error('Error fetching conversations:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleSelectConversation = (conv) => {
    selectedIdRef.current = conv.id;
    setSelectedConversation(conv);
  };

  const handleTransfer = async (conversationId) => {
    try {
      await axios.post(`${API}/conversations/${conversationId}/transfer`, {}, getAuthHeader());
      toast.success('Conversa transferida para atendimento humano');
      fetchConversations();
    } catch (error) {
      toast.error('Erro ao transferir conversa');
      console.error('Error transferring conversation:', error);
    }
  };

  const handleClose = async (conversationId) => {
    try {
      await axios.post(`${API}/conversations/${conversationId}/close`, {}, getAuthHeader());
      toast.success('Conversa encerrada');
      setSelectedConversation(null);
      fetchConversations();
    } catch (error) {
      toast.error('Erro ao encerrar conversa');
      console.error('Error closing conversation:', error);
    }
  };

  const handleDelete = async (conversationId, e) => {
    e.stopPropagation(); // Prevent card click
    if (!window.confirm('Tem certeza que deseja excluir esta conversa? Esta ação não pode ser desfeita.')) {
      return;
    }
    try {
      await axios.delete(`${API}/conversations/${conversationId}`, getAuthHeader());
      toast.success('Conversa excluída');
      if (selectedConversation?.id === conversationId) {
        setSelectedConversation(null);
      }
      fetchConversations();
    } catch (error) {
      toast.error('Erro ao excluir conversa');
      console.error('Error deleting conversation:', error);
    }
  };

  const handleSendMessage = async () => {
    if (!message.trim() || !selectedConversation) return;
    
    try {
      await axios.post(
        `${API}/send-message`,
        {
          phone_number: selectedConversation.phone_number,
          message: message
        },
        getAuthHeader()
      );
      setMessage('');
      toast.success('Mensagem enviada');
      fetchConversations();
    } catch (error) {
      toast.error('Erro ao enviar mensagem');
      console.error('Error sending message:', error);
    }
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'active': return 'bg-primary/20 text-primary border-primary/30';
      case 'transferred': return 'bg-amber-500/20 text-amber-500 border-amber-500/30';
      case 'closed': return 'bg-zinc-500/20 text-zinc-500 border-zinc-500/30';
      default: return '';
    }
  };

  const getStatusLabel = (status) => {
    switch (status) {
      case 'active': return 'Ativo';
      case 'transferred': return 'Transferido';
      case 'closed': return 'Encerrado';
      default: return status;
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
    <div className="h-screen flex flex-col" data-testid="conversations-page">
      <div className="p-6 md:p-8 border-b border-border">
        <h1 className="text-4xl font-bold mb-2">Conversas</h1>
        <p className="text-muted-foreground">Monitore e gerencie atendimentos</p>
      </div>

      <div className="flex-1 flex overflow-hidden">
        {/* Conversation List */}
        <div className="w-96 border-r border-border flex flex-col">
          <div className="p-4 border-b border-border">
            <Tabs value={filter} onValueChange={setFilter}>
              <TabsList className="grid w-full grid-cols-3">
                <TabsTrigger value="all" data-testid="filter-all">Todas</TabsTrigger>
                <TabsTrigger value="active" data-testid="filter-active">Ativas</TabsTrigger>
                <TabsTrigger value="transferred" data-testid="filter-transferred">Transferidas</TabsTrigger>
              </TabsList>
            </Tabs>
          </div>

          <ScrollArea className="flex-1">
            {conversations.length === 0 ? (
              <div className="p-8 text-center text-muted-foreground">
                Nenhuma conversa encontrada
              </div>
            ) : (
              <div className="space-y-2 p-4">
                {conversations.map((conv) => (
                  <Card
                    key={conv.id}
                    className={`cursor-pointer hover:border-zinc-700 transition-colors relative ${
                      selectedConversation?.id === conv.id ? 'border-primary' : ''
                    }`}
                    onClick={() => handleSelectConversation(conv)}
                    data-testid={`conversation-item-${conv.id}`}
                  >
                    <CardContent className="p-4">
                      <div className="flex justify-between items-start mb-2">
                        <div className="flex items-center gap-2 flex-1 min-w-0">
                          <div className="w-10 h-10 rounded-full bg-primary/20 flex items-center justify-center flex-shrink-0">
                            <User className="w-5 h-5 text-primary" />
                          </div>
                          <div className="min-w-0 flex-1">
                            <p className="font-semibold">{conv.user_name}</p>
                            <p className="text-xs text-muted-foreground">{conv.phone_number}</p>
                          </div>
                        </div>
                        <div className="flex items-center gap-2 flex-shrink-0">
                          <Badge className={getStatusColor(conv.status)}>
                            {getStatusLabel(conv.status)}
                          </Badge>
                          {/* Delete Button */}
                          <button
                            onClick={(e) => handleDelete(conv.id, e)}
                            className="w-7 h-7 rounded-full bg-red-500/20 hover:bg-red-500 flex items-center justify-center transition-colors"
                            data-testid={`delete-conversation-${conv.id}`}
                            title="Excluir conversa"
                          >
                            <X className="w-4 h-4 text-red-500 hover:text-white" />
                          </button>
                        </div>
                      </div>
                      {conv.messages.length > 0 && (
                        <p className="text-sm text-muted-foreground break-words">
                          {conv.messages[conv.messages.length - 1].content}
                        </p>
                      )}
                    </CardContent>
                  </Card>
                ))}
              </div>
            )}
          </ScrollArea>
        </div>

        {/* Chat Window */}
        <div className="flex-1 flex flex-col">
          {selectedConversation ? (
            <>
              {/* Chat Header */}
              <div className="p-4 border-b border-border flex justify-between items-center">
                <div className="flex items-center gap-3">
                  <div className="w-12 h-12 rounded-full bg-primary/20 flex items-center justify-center">
                    <User className="w-6 h-6 text-primary" />
                  </div>
                  <div>
                    <h3 className="font-semibold text-lg">{selectedConversation.user_name}</h3>
                    <p className="text-sm text-muted-foreground">{selectedConversation.phone_number}</p>
                  </div>
                </div>
                <div className="flex gap-2">
                  {!selectedConversation.transferred_to_human && selectedConversation.status === 'active' && (
                    <Button
                      variant="outline"
                      onClick={() => handleTransfer(selectedConversation.id)}
                      className="gap-2"
                      data-testid="transfer-conversation-button"
                    >
                      <ArrowRight className="w-4 h-4" />
                      Transferir
                    </Button>
                  )}
                  {selectedConversation.status !== 'closed' && (
                    <Button
                      variant="outline"
                      onClick={() => handleClose(selectedConversation.id)}
                      className="gap-2"
                      data-testid="close-conversation-button"
                    >
                      <X className="w-4 h-4" />
                      Encerrar
                    </Button>
                  )}
                </div>
              </div>

              {/* Messages */}
              <ScrollArea className="flex-1 p-6">
                <div className="space-y-4">
                  {selectedConversation.messages.map((msg, idx) => (
                    <div
                      key={idx}
                      className={`flex ${msg.sender === 'user' ? 'justify-start' : 'justify-end'}`}
                      data-testid={`message-${idx}`}
                    >
                      <div
                        className={`max-w-md rounded-lg p-4 ${
                          msg.sender === 'user'
                            ? 'bg-secondary'
                            : msg.sender === 'agent'
                            ? 'bg-amber-500/20'
                            : 'bg-primary/20'
                        }`}
                      >
                        <div className="flex items-center gap-2 mb-1">
                          {msg.sender === 'user' ? (
                            <User className="w-4 h-4" />
                          ) : msg.sender === 'agent' ? (
                            <User className="w-4 h-4 text-amber-500" />
                          ) : (
                            <Bot className="w-4 h-4 text-primary" />
                          )}
                          <span className="text-xs font-medium">
                            {msg.sender === 'user' ? 'Usuário' : msg.sender === 'agent' ? 'Agente' : 'Bot'}
                          </span>
                          <span className="text-xs text-muted-foreground">
                            {new Date(msg.timestamp).toLocaleTimeString('pt-BR', {
                              hour: '2-digit',
                              minute: '2-digit'
                            })}
                          </span>
                        </div>
                        <p className="text-sm whitespace-pre-wrap">{msg.content}</p>
                      </div>
                    </div>
                  ))}
                  {/* Invisible element to scroll to */}
                  <div ref={messagesEndRef} />
                </div>
              </ScrollArea>

              {/* Message Input (only for transferred conversations) */}
              {selectedConversation.transferred_to_human && selectedConversation.status !== 'closed' && (
                <div className="sticky bottom-0 p-4 border-t border-border bg-background" style={{ marginBottom: '60px' }}>
                  <div className="flex gap-2">
                    <Input
                      placeholder="Digite sua mensagem..."
                      value={message}
                      onChange={(e) => setMessage(e.target.value)}
                      onKeyPress={(e) => e.key === 'Enter' && handleSendMessage()}
                      data-testid="message-input"
                      className="flex-1"
                    />
                    <Button onClick={handleSendMessage} className="gap-2 shrink-0" data-testid="send-message-button">
                      <Send className="w-4 h-4" />
                      Enviar
                    </Button>
                  </div>
                </div>
              )}
            </>
          ) : (
            <div className="flex-1 flex items-center justify-center">
              <div className="text-center">
                <MessageSquare className="w-16 h-16 text-muted-foreground mx-auto mb-4" />
                <p className="text-muted-foreground">Selecione uma conversa para visualizar</p>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default Conversations;