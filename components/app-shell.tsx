"use client";

import { usePathname } from "next/navigation";
import { Sidebar } from "@/components/sidebar";
import { Header } from "@/components/header";

export function AppShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();

  if (pathname === "/login") {
    return <>{children}</>;
  }

  return (
    <div className="h-full relative">
      <div className="hidden h-full md:flex md:w-72 md:flex-col md:fixed md:inset-y-0 z-[80] bg-zinc-900 dark:bg-zinc-950">
        <Sidebar />
      </div>
      <main className="md:pl-72 bg-zinc-50 dark:bg-zinc-900 min-h-screen">
        <Header />
        <div className="p-8">{children}</div>
      </main>
    </div>
  );
}
