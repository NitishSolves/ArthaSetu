import { useState } from "react";
import { Home, BarChart3, Lightbulb, User, Menu, X, Wallet, DollarSign, AlertTriangle, Zap, LogOut } from "lucide-react";
import { useNavigate, useLocation } from "react-router-dom";
import { useApp } from "@/contexts/AppContext";
import { cn } from "@/lib/utils";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
  DropdownMenuLabel,
} from "@/components/ui/dropdown-menu";

const BottomNav = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const { logout } = useApp();
  const [moreMenuOpen, setMoreMenuOpen] = useState(false);

  const navItems = [
    { icon: Home, label: "Home", path: "/dashboard" },
    { icon: BarChart3, label: "Stats", path: "/stats" },
    { icon: Lightbulb, label: "Tips", path: "/tips" },
    { icon: User, label: "Profile", path: "/profile" },
  ];

  const moreItems = [
    { icon: Wallet, label: "Budget", path: "/budget" },
    { icon: DollarSign, label: "Tax Planning", path: "/tax" },
    { icon: AlertTriangle, label: "Risk Analysis", path: "/risk" },
    { icon: Zap, label: "Action Plan", path: "/actions" },
  ];

  const handleLogout = () => {
    logout();
    navigate("/");
  };

  return (
    <nav className="fixed bottom-0 left-0 right-0 bg-card border-t border-border z-50">
      <div className="max-w-lg mx-auto px-4">
        <div className="flex justify-between items-center h-16">
          {/* Main Nav Items */}
          <div className="flex justify-around items-center flex-1">
            {navItems.map(({ icon: Icon, label, path }) => {
              const isActive = location.pathname === path;
              return (
                <button
                  key={path}
                  onClick={() => navigate(path)}
                  className={cn(
                    "flex flex-col items-center justify-center gap-1 min-w-[60px] transition-colors",
                    isActive ? "text-primary" : "text-muted-foreground"
                  )}
                >
                  <Icon className="w-5 h-5" />
                  <span className="text-xs font-medium">{label}</span>
                </button>
              );
            })}
          </div>

          {/* More Menu */}
          <DropdownMenu open={moreMenuOpen} onOpenChange={setMoreMenuOpen}>
            <DropdownMenuTrigger asChild>
              <button className="flex flex-col items-center justify-center gap-1 min-w-[60px] text-muted-foreground hover:text-primary transition-colors">
                <Menu className="w-5 h-5" />
                <span className="text-xs font-medium">More</span>
              </button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end" className="w-56">
              <DropdownMenuLabel>Financial Tools</DropdownMenuLabel>
              <DropdownMenuSeparator />
              {moreItems.map(({ icon: Icon, label, path }) => (
                <DropdownMenuItem
                  key={path}
                  onClick={() => {
                    navigate(path);
                    setMoreMenuOpen(false);
                  }}
                  className="cursor-pointer"
                >
                  <Icon className="w-4 h-4 mr-2" />
                  <span>{label}</span>
                </DropdownMenuItem>
              ))}
              <DropdownMenuSeparator />
              <DropdownMenuItem onClick={handleLogout} className="cursor-pointer text-red-600">
                <LogOut className="w-4 h-4 mr-2" />
                <span>Logout</span>
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        </div>
      </div>
    </nav>
  );
};

export default BottomNav;
