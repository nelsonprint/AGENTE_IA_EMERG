import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import { LayoutDashboard, Settings, MessageSquare, FileText, LogOut, Bot } from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { Button } from './ui/button';

const Sidebar = () => {
  const location = useLocation();
  const { logout, user } = useAuth();

  const navItems = [
    { path: '/dashboard', icon: LayoutDashboard, label: 'Dashboard' },
    { path: '/conversations', icon: MessageSquare, label: 'Conversas' },
    { path: '/prompts', icon: Bot, label: 'Prompts' },
    { path: '/settings', icon: Settings, label: 'Configurações' },
  ];

  return (
    <div className="w-64 min-h-screen bg-card border-r border-border flex flex-col" data-testid="sidebar">
      <div className="p-6 border-b border-border">
        <h1 className="text-2xl font-bold text-primary flex items-center gap-2" data-testid="app-title">
          <MessageSquare className="w-6 h-6" />
          WhatsApp Bot
        </h1>
      </div>

      <nav className="flex-1 p-4 space-y-2">
        {navItems.map((item) => {
          const Icon = item.icon;
          const isActive = location.pathname === item.path;
          return (
            <Link
              key={item.path}
              to={item.path}
              data-testid={`nav-${item.label.toLowerCase()}`}
            >
              <Button
                variant={isActive ? "default" : "ghost"}
                className="w-full justify-start gap-3"
              >
                <Icon className="w-5 h-5" />
                {item.label}
              </Button>
            </Link>
          );
        })}
      </nav>

      <div className="p-4 border-t border-border">
        <div className="mb-3 px-3">
          <p className="text-sm text-muted-foreground">Conectado como</p>
          <p className="text-sm font-medium text-foreground" data-testid="user-name">{user?.username}</p>
        </div>
        <Button
          variant="outline"
          className="w-full justify-start gap-3"
          onClick={logout}
          data-testid="logout-button"
        >
          <LogOut className="w-5 h-5" />
          Sair
        </Button>
      </div>
    </div>
  );
};

export default Sidebar;