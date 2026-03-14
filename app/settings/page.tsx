"use client"

import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Switch } from "@/components/ui/switch"
import { Skeleton } from "@/components/ui/skeleton"
import { Save, Database, Sun, Moon, Heart, RefreshCw, Trash2 } from "lucide-react"
import { AlertDialog, AlertDialogAction, AlertDialogCancel, AlertDialogContent, AlertDialogDescription, AlertDialogFooter, AlertDialogHeader, AlertDialogTitle, AlertDialogTrigger } from "@/components/ui/alert-dialog"
import { useTheme } from "next-themes"
import { useState } from "react"
import { seedDemoData, checkHealth } from "@/hooks/use-api"
import { toast } from "sonner"
import { API_URL } from "@/lib/config"
import useSWR from "swr"

interface HealthStatus {
  status: string
  database: string
  redis?: string
  timestamp: string
}

export default function SettingsPage() {
  const { theme, setTheme } = useTheme()
  const [seedLoading, setSeedLoading] = useState(false)
  const [clearLoading, setClearLoading] = useState(false)
  const { data: health, isLoading: healthLoading, mutate: refreshHealth } = useSWR<HealthStatus | null>(
    "settings-health",
    checkHealth,
    {
      revalidateOnFocus: false,
      revalidateOnReconnect: true,
      shouldRetryOnError: false,
    }
  )

  const handleSeedDemo = async () => {
    setSeedLoading(true)
    try {
      await seedDemoData()
      toast.success("Demo data seeded successfully!")
    } catch {
      toast.error("Failed to seed demo data")
    }
    setSeedLoading(false)
  }

  const handleClearData = async () => {
    setClearLoading(true)
    try {
      await fetch(`${API_URL}/api/leads/clear`, { method: 'DELETE' })
      toast.success("All leads cleared")
    } catch {
      toast.error("Failed to clear data")
    }
    setClearLoading(false)
  }

  return (
    <div className="space-y-6 max-w-4xl mx-auto">
      <div>
        <h2 className="text-3xl font-bold tracking-tight">Settings</h2>
        <p className="text-zinc-500 dark:text-zinc-400 mt-1">Configure your automated lead engine.</p>
      </div>

      <div className="grid gap-6">
        {/* System Health */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Heart className="h-5 w-5 text-red-500" />
              System Health
            </CardTitle>
            <CardDescription>
              Check the status of backend services.
            </CardDescription>
          </CardHeader>
          <CardContent>
            {healthLoading || typeof health === 'undefined' ? (
              <div className="space-y-2">
                <Skeleton className="h-6 w-48" />
                <Skeleton className="h-4 w-32" />
              </div>
            ) : health ? (
              <div className="space-y-3">
                <div className="flex items-center gap-2">
                  <div className={`w-3 h-3 rounded-full ${health.status === 'healthy' ? 'bg-emerald-500' : 'bg-red-500'}`} />
                  <span className="font-medium capitalize">{health.status}</span>
                </div>
                <div className="grid grid-cols-2 gap-4 text-sm">
                  <div>
                    <span className="text-zinc-500 dark:text-zinc-400">Database:</span>
                    <span className={`ml-2 font-medium ${health.database === 'connected' ? 'text-emerald-600' : 'text-red-600'}`}>
                      {health.database}
                    </span>
                  </div>
                  {health.redis && (
                    <div>
                      <span className="text-zinc-500 dark:text-zinc-400">Redis:</span>
                      <span className={`ml-2 font-medium ${health.redis === 'connected' ? 'text-emerald-600' : 'text-amber-600'}`}>
                        {health.redis}
                      </span>
                    </div>
                  )}
                </div>
                <p className="text-xs text-zinc-400 dark:text-zinc-500">
                  Last checked: {new Date(health.timestamp).toLocaleString()}
                </p>
              </div>
            ) : (
              <div className="text-red-500 dark:text-red-400">
                Unable to connect to backend. Is the server running?
              </div>
            )}
          </CardContent>
          <CardFooter className="border-t pt-4">
            <Button variant="outline" onClick={() => refreshHealth()} disabled={healthLoading}>
              <RefreshCw className={`mr-2 h-4 w-4 ${healthLoading ? 'animate-spin' : ''}`} />
              Check Again
            </Button>
          </CardFooter>
        </Card>

        {/* Appearance */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              {theme === 'dark' ? <Moon className="h-5 w-5" /> : <Sun className="h-5 w-5" />}
              Appearance
            </CardTitle>
            <CardDescription>
              Customize the look and feel of the dashboard.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="flex items-center justify-between">
              <div>
                <Label htmlFor="dark-mode">Dark Mode</Label>
                <p className="text-sm text-zinc-500 dark:text-zinc-400">Toggle between light and dark themes</p>
              </div>
              <Switch
                id="dark-mode"
                checked={theme === 'dark'}
                onCheckedChange={(checked) => setTheme(checked ? 'dark' : 'light')}
              />
            </div>
          </CardContent>
        </Card>

        {/* Demo Data */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Database className="h-5 w-5" />
              Demo Data
            </CardTitle>
            <CardDescription>
              Seed sample data for testing or clear all leads.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <p className="text-sm text-zinc-500 dark:text-zinc-400">
              Seed demo data to populate the dashboard with sample leads and jobs for testing purposes.
            </p>
          </CardContent>
          <CardFooter className="border-t pt-4 flex gap-2">
            <Button onClick={handleSeedDemo} disabled={seedLoading}>
              {seedLoading ? (
                <RefreshCw className="mr-2 h-4 w-4 animate-spin" />
              ) : (
                <Database className="mr-2 h-4 w-4" />
              )}
              Seed Demo Data
            </Button>
            <AlertDialog>
              <AlertDialogTrigger asChild>
                <Button variant="destructive" disabled={clearLoading}>
                  <Trash2 className="mr-2 h-4 w-4" />
                  Clear All Leads
                </Button>
              </AlertDialogTrigger>
              <AlertDialogContent>
                <AlertDialogHeader>
                  <AlertDialogTitle>Clear all leads?</AlertDialogTitle>
                  <AlertDialogDescription>
                    This will permanently delete ALL leads from the database. This action cannot be undone.
                  </AlertDialogDescription>
                </AlertDialogHeader>
                <AlertDialogFooter>
                  <AlertDialogCancel>Cancel</AlertDialogCancel>
                  <AlertDialogAction onClick={handleClearData} className="bg-red-600 hover:bg-red-700">
                    Clear All
                  </AlertDialogAction>
                </AlertDialogFooter>
              </AlertDialogContent>
            </AlertDialog>
          </CardFooter>
        </Card>

        {/* Scraping Configuration */}
        <Card>
          <CardHeader>
            <CardTitle>Scraping Configuration</CardTitle>
            <CardDescription>
              Adjust the anti-blocking strategy and worker settings. These are stored as environment variables on the backend.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="delayMin">Min Delay (seconds)</Label>
                <Input id="delayMin" type="number" defaultValue="2" disabled className="bg-zinc-50 dark:bg-zinc-800" />
                <p className="text-xs text-zinc-400">ENV: SCRAPE_DELAY_MIN</p>
              </div>
              <div className="space-y-2">
                <Label htmlFor="delayMax">Max Delay (seconds)</Label>
                <Input id="delayMax" type="number" defaultValue="5" disabled className="bg-zinc-50 dark:bg-zinc-800" />
                <p className="text-xs text-zinc-400">ENV: SCRAPE_DELAY_MAX</p>
              </div>
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="discoveryWorkers">Discovery Workers</Label>
                <Input id="discoveryWorkers" type="number" defaultValue="2" disabled className="bg-zinc-50 dark:bg-zinc-800" />
                <p className="text-xs text-zinc-400">ENV: DISCOVERY_WORKERS</p>
              </div>
              <div className="space-y-2">
                <Label htmlFor="fetchWorkers">Detail Fetch Workers</Label>
                <Input id="fetchWorkers" type="number" defaultValue="6" disabled className="bg-zinc-50 dark:bg-zinc-800" />
                <p className="text-xs text-zinc-400">ENV: FETCH_WORKERS</p>
              </div>
            </div>
            <p className="text-sm text-amber-600 dark:text-amber-400 bg-amber-50 dark:bg-amber-950 p-3 rounded-lg">
              Note: These settings are configured via environment variables on the backend. Edit your .env file or Docker configuration to change them.
            </p>
          </CardContent>
        </Card>

        {/* Lead Scoring Model */}
        <Card>
          <CardHeader>
            <CardTitle>Lead Scoring Model</CardTitle>
            <CardDescription>
              Current scoring weights for lead classification. Configure via backend environment variables.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label>No Website</Label>
                <div className="p-3 bg-red-50 dark:bg-red-950 rounded-lg">
                  <span className="text-xl font-bold text-red-600 dark:text-red-400">+4 points</span>
                </div>
              </div>
              <div className="space-y-2">
                <Label>Needs Redesign</Label>
                <div className="p-3 bg-amber-50 dark:bg-amber-950 rounded-lg">
                  <span className="text-xl font-bold text-amber-600 dark:text-amber-400">+2 points</span>
                </div>
              </div>
              <div className="space-y-2">
                <Label>Rating above 4</Label>
                <div className="p-3 bg-emerald-50 dark:bg-emerald-950 rounded-lg">
                  <span className="text-xl font-bold text-emerald-600 dark:text-emerald-400">+2 points</span>
                </div>
              </div>
              <div className="space-y-2">
                <Label>Reviews above 20</Label>
                <div className="p-3 bg-blue-50 dark:bg-blue-950 rounded-lg">
                  <span className="text-xl font-bold text-blue-600 dark:text-blue-400">+1 point</span>
                </div>
              </div>
              <div className="space-y-2">
                <Label>Phone available</Label>
                <div className="p-3 bg-purple-50 dark:bg-purple-950 rounded-lg">
                  <span className="text-xl font-bold text-purple-600 dark:text-purple-400">+1 point</span>
                </div>
              </div>
            </div>
            <p className="text-sm text-zinc-500 dark:text-zinc-400">
              Maximum score: 8 points. Leads with score ≥5 are considered qualified.
            </p>
          </CardContent>
        </Card>

        {/* API Configuration */}
        <Card>
          <CardHeader>
            <CardTitle>API Configuration</CardTitle>
            <CardDescription>
              Backend API endpoint configuration.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <Label>API URL</Label>
              <Input value={API_URL} disabled className="font-mono bg-zinc-50 dark:bg-zinc-800" />
              <p className="text-xs text-zinc-400 dark:text-zinc-500">
                Edit lib/config.ts or set NEXT_PUBLIC_API_URL environment variable to change.
              </p>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
