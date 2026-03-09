"use strict";
import { Bell, Search, User } from "lucide-react";
import { Input } from "@/components/ui/input";

export function Header() {
  return (
    <div className="flex items-center p-4 border-b h-16 bg-white">
      <div className="flex items-center w-full justify-between">
        <div className="flex items-center bg-zinc-100 rounded-md px-3 py-1.5 w-96">
          <Search className="h-4 w-4 text-zinc-500 mr-2" />
          <input
            className="bg-transparent border-none outline-none text-sm w-full"
            placeholder="Search leads, jobs, or businesses..."
          />
        </div>
        <div className="flex items-center space-x-4">
          <button className="relative p-2 text-zinc-500 hover:bg-zinc-100 rounded-full">
            <Bell className="h-5 w-5" />
            <span className="absolute top-1.5 right-1.5 h-2 w-2 bg-red-500 rounded-full"></span>
          </button>
          <div className="h-8 w-8 bg-indigo-500 rounded-full flex items-center justify-center text-white font-medium text-sm">
            US
          </div>
        </div>
      </div>
    </div>
  );
}
