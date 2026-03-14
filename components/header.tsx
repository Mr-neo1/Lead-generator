"use client";
import { Bell, Search, Sun, Moon, LogOut } from "lucide-react";
import { Button } from "@/components/ui/button";
import { useTheme } from "next-themes";

export function Header() {
  const { theme, setTheme } = useTheme();

  const handleLogout = async () => {
    await fetch("/api/auth/logout", { method: "POST" });
    window.location.href = "/login";
  };

  return (
    <div className="flex items-center p-4 border-b h-16 bg-white dark:bg-zinc-950 dark:border-zinc-800">
      <div className="flex items-center w-full justify-between">
        <div className="flex items-center bg-zinc-100 dark:bg-zinc-800 rounded-md px-3 py-1.5 w-96">
          <Search className="h-4 w-4 text-zinc-500 dark:text-zinc-400 mr-2" />
          <input
            className="bg-transparent border-none outline-none text-sm w-full dark:text-zinc-100 dark:placeholder:text-zinc-500"
            placeholder="Search leads, jobs, or businesses..."
          />
        </div>
        <div className="flex items-center space-x-2">
          <Button
            variant="ghost"
            size="icon"
            onClick={() => setTheme(theme === "dark" ? "light" : "dark")}
            className="text-zinc-500 hover:text-zinc-700 dark:text-zinc-400 dark:hover:text-zinc-200"
          >
            {theme === "dark" ? (
              <Sun className="h-5 w-5" />
            ) : (
              <Moon className="h-5 w-5" />
            )}
          </Button>
          <button className="relative p-2 text-zinc-500 hover:bg-zinc-100 dark:hover:bg-zinc-800 rounded-full">
            <Bell className="h-5 w-5" />
            <span className="absolute top-1.5 right-1.5 h-2 w-2 bg-red-500 rounded-full"></span>
          </button>
          <div className="h-8 w-8 bg-indigo-500 rounded-full flex items-center justify-center text-white font-medium text-sm">
            US
          </div>
          <Button
            variant="ghost"
            size="icon"
            onClick={handleLogout}
            className="text-zinc-500 hover:text-zinc-700 dark:text-zinc-400 dark:hover:text-zinc-200"
            aria-label="Log out"
            title="Log out"
          >
            <LogOut className="h-5 w-5" />
          </Button>
        </div>
      </div>
    </div>
  );
}
