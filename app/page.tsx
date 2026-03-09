"use client"

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Activity, Briefcase, Globe, Users } from "lucide-react"
import { useEffect, useState } from "react"
import { API_URL } from "@/lib/config"

interface Stats {
  totalBusinesses: number
  qualifiedLeads: number
  demoSites: number
  activeJobs: number
}

interface Job {
  job_id: string
  keyword: string
  location: string
  status: string
}

export default function DashboardPage() {
  const [stats, setStats] = useState<Stats>({ totalBusinesses: 0, qualifiedLeads: 0, demoSites: 0, activeJobs: 0 })
  const [jobs, setJobs] = useState<Job[]>([])

  useEffect(() => {
    fetch(`${API_URL}/api/stats`).then(r => r.json()).then(setStats).catch(console.error)
    fetch(`${API_URL}/api/jobs`).then(r => r.json()).then(setJobs).catch(console.error)
  }, [])

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h2 className="text-3xl font-bold tracking-tight">Dashboard</h2>
      </div>

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Businesses</CardTitle>
            <Briefcase className="h-4 w-4 text-zinc-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats.totalBusinesses.toLocaleString()}</div>
            <p className="text-xs text-zinc-500">From scraped data</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Qualified Leads</CardTitle>
            <Users className="h-4 w-4 text-zinc-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats.qualifiedLeads.toLocaleString()}</div>
            <p className="text-xs text-zinc-500">Score ≥ 5</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Demo Sites Generated</CardTitle>
            <Globe className="h-4 w-4 text-zinc-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats.demoSites.toLocaleString()}</div>
            <p className="text-xs text-zinc-500">Ready to show</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Active Jobs</CardTitle>
            <Activity className="h-4 w-4 text-zinc-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats.activeJobs}</div>
            <p className="text-xs text-zinc-500">Currently running</p>
          </CardContent>
        </Card>
      </div>

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-7">
        <Card className="col-span-4">
          <CardHeader>
            <CardTitle>Lead Generation Overview</CardTitle>
          </CardHeader>
          <CardContent className="pl-2">
            <div className="h-[300px] w-full flex items-center justify-center border-2 border-dashed border-zinc-200 rounded-lg bg-zinc-50 text-zinc-500">
              [Chart Placeholder: Leads over time]
            </div>
          </CardContent>
        </Card>
        <Card className="col-span-3">
          <CardHeader>
            <CardTitle>Recent Jobs</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-8">
              {jobs.length > 0 ? jobs.slice(0, 4).map((job, i) => (
                <div key={job.job_id} className="flex items-center">
                  <div className="space-y-1 flex-1">
                    <p className="text-sm font-medium leading-none">{job.keyword} in {job.location}</p>
                    <p className="text-sm text-zinc-500">
                      Status: <span className={job.status === 'completed' ? 'text-emerald-500' : job.status === 'running' ? 'text-blue-500' : 'text-amber-500'}>{job.status}</span>
                    </p>
                  </div>
                </div>
              )) : (
                <p className="text-sm text-zinc-500">No jobs yet. Create one to get started!</p>
              )}
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
