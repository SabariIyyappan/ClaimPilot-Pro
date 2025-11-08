import { Link, useLocation } from 'react-router-dom';
import { Badge } from '@/components/ui/badge';
import { Brain, HelpCircle, User } from 'lucide-react';
import { cn } from '@/lib/utils';

export function Header() {
  const location = useLocation();

  const navItems = [
    { path: '/upload', label: 'Upload' },
    { path: '/suggest', label: 'Suggestions' },
    { path: '/review', label: 'Review' },
    { path: '/claims', label: 'Claims' },
    { path: '/about', label: 'About' },
  ];

  const isActive = (path: string) => location.pathname === path;

  return (
    <header className="border-b bg-card/50 backdrop-blur-sm sticky top-0 z-50">
      <div className="container mx-auto max-w-7xl">
        <div className="flex items-center justify-between h-16 px-4">
          <div className="flex items-center gap-8">
            <Link to="/upload" className="flex items-center gap-2 hover:opacity-80 transition-opacity">
              <Brain className="h-7 w-7 text-primary" />
              <span className="text-xl font-bold">ClaimPilot Pro</span>
            </Link>

            <nav className="hidden md:flex items-center gap-1">
              {navItems.map((item) => (
                <Link
                  key={item.path}
                  to={item.path}
                  className={cn(
                    'px-4 py-2 rounded-md text-base font-medium transition-colors',
                    isActive(item.path)
                      ? 'bg-primary text-primary-foreground'
                      : 'text-muted-foreground hover:text-foreground hover:bg-accent'
                  )}
                >
                  {item.label}
                </Link>
              ))}
            </nav>
          </div>

          <div className="flex items-center gap-4">
            <Badge variant="secondary" className="hidden sm:flex">
              Sandbox
            </Badge>
            <button
              className="text-muted-foreground hover:text-foreground transition-colors"
              aria-label="Help"
            >
              <HelpCircle className="h-5 w-5" />
            </button>
            <button
              className="text-muted-foreground hover:text-foreground transition-colors"
              aria-label="User menu"
            >
              <User className="h-5 w-5" />
            </button>
          </div>
        </div>
      </div>
    </header>
  );
}
