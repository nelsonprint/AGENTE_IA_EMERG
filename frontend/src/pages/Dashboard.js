import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { useAuth } from '../context/AuthContext';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { MessageSquare, Users, TrendingUp, UserCheck } from 'lucide-react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

const Dashboard = () => {
  const { getAuthHeader } = useAuth();
  const [stats, setStats] = useState({
    active_conversations: 0,
    transferred_conversations: 0,
    messages_today: 0,
    total_users: 0
  });
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchStats();
  }, []);

  const fetchStats = async () => {
    try {
      const response = await axios.get(`${API}/dashboard/stats`, getAuthHeader());
      setStats(response.data);
    } catch (error) {
      console.error('Error fetching stats:', error);
    } finally {
      setLoading(false);
    }
  };

  const chartData = [
    { name: 'Conversas Ativas', value: stats.active_conversations },
    { name: 'Transferidas', value: stats.transferred_conversations },
    { name: 'Mensagens Hoje', value: stats.messages_today },
  ];

  const StatCard = ({ title, value, icon: Icon, color }) => (
    <Card className="hover:border-zinc-700 transition-colors" data-testid={`stat-card-${title.toLowerCase().replace(/\s/g, '-')}`}>
      <CardHeader className="flex flex-row items-center justify-between pb-2">
        <CardTitle className="text-sm font-medium text-muted-foreground">{title}</CardTitle>
        <div className={`w-10 h-10 rounded-full bg-${color}/20 flex items-center justify-center`}>
          <Icon className={`w-5 h-5 text-${color}`} />
        </div>
      </CardHeader>
      <CardContent>
        <div className="text-3xl font-bold" data-testid={`stat-value-${title.toLowerCase().replace(/\s/g, '-')}`}>{value}</div>
      </CardContent>
    </Card>
  );

  if (loading) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="text-muted-foreground">Carregando...</div>
      </div>
    );
  }

  return (
    <div className="p-6 md:p-8 space-y-6" data-testid="dashboard-page">
      <div>
        <h1 className="text-4xl font-bold mb-2">Dashboard</h1>
        <p className="text-muted-foreground">Visão geral do seu assistente WhatsApp</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          title="Conversas Ativas"
          value={stats.active_conversations}
          icon={MessageSquare}
          color="primary"
        />
        <StatCard
          title="Transferidas"
          value={stats.transferred_conversations}
          icon={UserCheck}
          color="amber-500"
        />
        <StatCard
          title="Mensagens Hoje"
          value={stats.messages_today}
          icon={TrendingUp}
          color="blue-500"
        />
        <StatCard
          title="Total de Usuários"
          value={stats.total_users}
          icon={Users}
          color="violet-500"
        />
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Visão Geral</CardTitle>
        </CardHeader>
        <CardContent>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={chartData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#27272a" />
              <XAxis dataKey="name" stroke="#a1a1aa" />
              <YAxis stroke="#a1a1aa" />
              <Tooltip 
                contentStyle={{ 
                  backgroundColor: '#18181b', 
                  border: '1px solid #27272a',
                  borderRadius: '8px'
                }} 
              />
              <Bar dataKey="value" fill="#10b981" radius={[8, 8, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </CardContent>
      </Card>
    </div>
  );
};

export default Dashboard;