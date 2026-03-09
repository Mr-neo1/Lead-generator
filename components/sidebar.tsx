"use client";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { LayoutDashboard, List, PlusCircle, Settings, Users } from "lucide-react";
import { cn } from "@/lib/utils";

const routes = [
  {
    label: "Dashboard",
    icon: LayoutDashboard,
    href: "/",
    color: "text-zinc-500",
  },
  {
    label: "Scraping Jobs",
    icon: List,
    href: "/jobs",
    color: "text-zinc-500",
  },
  {
    label: "New Job",
    icon: PlusCircle,
    href: "/jobs/new",
    color: "text-zinc-500",
  },
  {
    label: "Leads",
    icon: Users,
    href: "/leads",
    color: "text-zinc-500",
  },
  {
    label: "Settings",
    icon: Settings,
    href: "/settings",
    color: "text-zinc-500",
  },
];

export function Sidebar() {
  const pathname = usePathname();

  return (
    <div className="space-y-4 py-4 flex flex-col h-full bg-zinc-900 text-white">
      <div className="px-3 py-2 flex-1">
        <Link href="/" className="flex items-center pl-3 mb-14">
          <div className="relative w-8 h-8 mr-4 flex items-center justify-center bg-indigo-500 rounded-lg">
            <LayoutDashboard className="h-5 w-5 text-white" />
          </div>
          <h1 className="text-xl font-bold">Lead Engine</h1>
        </Link>
        <div className="space-y-1">
          {routes.map((route) => (
            <Link
              key={route.href}
              href={route.href}
              className={cn(
                "text-sm group flex p-3 w-full justify-start font-medium cursor-pointer hover:text-white hover:bg-white/10 rounded-lg transition",
                pathname === route.href ? "text-white bg-white/10" : "text-zinc-400"
              )}
            >
              <div className="flex items-center flex-1">
                <route.icon className={cn("h-5 w-5 mr-3", route.color)} />
                {route.label}
              </div>
            </Link>
          ))}
        </div>
      </div>
    </div>
  );
}
