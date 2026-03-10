"use client"

import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import { Badge } from "@/components/ui/badge"
import { PlusCircle, Play, Pause, Trash2, RefreshCw, MapPin, Search } from "lucide-react"
import Link from "next/link"
import { useEffect, useState, useCallback } from "react"
import { API_URL } from "@/lib/config"

interface Job {
  job_id: string
  keyword: string
  location: string
  radius: number
  grid_size: string
  status: string
  total_tasks: number
  completed_tasks: number
  leads_found: number
  created_at: string | null
}

export default function JobsPage() {
  const [jobs, setJobs] = useState<Job[]>([])
  const [loading, setLoading] = useState(true)
  const [actionLoading, setActionLoading] = useState<string | null>(null)

  const fetchJobs = useCallback(() => {
    fetch(`${API_URL}/api/jobs`)
      .then(r => r.json())
      .then(data => {
        setJobs(data)
        setLoading(false)
      })
      .catch(err => {
        console.error(err)
        setLoading(false)
      })
  }, [])

  useEffect(() => {
    fetchJobs()
    // Auto-refresh every 10 seconds for running jobs
    const interval = setInterval(fetchJobs, 10000)
    return () => clearInterval(interval)
  }, [fetchJobs])

  const handlePause = async (jobId: string) => {
    setActionLoading(jobId)
    try {
      await fetch(`${API_URL}/api/jobs/${jobId}/pause`, { method: 'POST' })
      fetchJobs()
    } catch (err) {
      console.error(err)
    }
    setActionLoading(null)
  }

  const handleResume = async (jobId: string) => {
    setActionLoading(jobId)
    try {
      await fetch(`${API_URL}/api/jobs/${jobId}/resume`, { method: 'POST' })
      fetchJobs()
    } catch (err) {
      console.error(err)
    }
    setActionLoading(null)
  }

  const handleRestart = async (jobId: string) => {
    setActionLoading(jobId)
    try {
      await fetch(`${API_URL}/api/jobs/${jobId}/restart`, { method: 'POST' })
      fetchJobs()
    } catch (err) {
      console.error(err)
    }
    setActionLoading(null)
  }

  const handleDelete = async (jobId: string) => {
    if (!confirm(`Delete job ${jobId}? This cannot be undone.`)) return
    setActionLoading(jobId)
    try {
      await fetch(`${API_URL}/api/jobs/${jobId}`, { method: 'DELETE' })
      fetchJobs()
    } catch (err) {
      console.error(err)
    }
    setActionLoading(null)
  }

  const getStatusBadge = (status: string) => {
    const variants: Record<string, "default" | "secondary" | "destructive" | "outline"> = {
      completed: "default",
      running: "secondary", 
      paused: "outline",
      failed: "destructive",
      pending: "outline"
    }
    const colors: Record<string, string> = {
      completed: "bg-emerald-100 text-emerald-700 border-emerald-200",
      running: "bg-blue-100 text-blue-700 border-blue-200 animate-pulse",
      paused: "bg-amber-100 text-amber-700 border-amber-200",
      failed: "bg-red-100 text-red-700 border-red-200",
      pending: "bg-zinc-100 text-zinc-600 border-zinc-200"
    }
    return (
      <Badge variant={variants[status] || "outline"} className={colors[status] || ""}>
        {status}
      </Badge>
    )
  }

  const runningJobs = jobs.filter(j => j.status === "running").length
  const completedJobs = jobs.filter(j => j.status === "completed").length
  const totalLeads = jobs.reduce((sum, j) => sum + (j.leads_found || 0), 0)
  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h2 className="text-3xl font-bold tracking-tight">Scraping Jobs</h2>
          <p className="text-zinc-500 mt-1">Manage your automated lead generation jobs.</p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" onClick={fetchJobs} disabled={loading}>
            <RefreshCw className={`mr-2 h-4 w-4 ${loading ? 'animate-spin' : ''}`} />
            Refresh
          </Button>
          <Button asChild>
            <Link href="/jobs/new">
              <PlusCircle className="mr-2 h-4 w-4" />
              New Job
            </Link>
          </Button>
        </div>
      </div>

      {/* Quick Stats */}
      <div className="grid grid-cols-3 gap-4">
        <Card className="bg-blue-50 border-blue-100">
          <CardContent className="pt-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-blue-600">Running</p>
                <p className="text-2xl font-bold text-blue-700">{runningJobs}</p>
              </div>
              <div className="p-2 bg-blue-100 rounded-full">
                <RefreshCw className="h-5 w-5 text-blue-600 animate-spin" />
              </div>
            </div>
          </CardContent>
        </Card>
        <Card className="bg-emerald-50 border-emerald-100">
          <CardContent className="pt-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-emerald-600">Completed</p>
                <p className="text-2xl font-bold text-emerald-700">{completedJobs}</p>
              </div>
              <div className="p-2 bg-emerald-100 rounded-full">
                <Search className="h-5 w-5 text-emerald-600" />
              </div>
            </div>
          </CardContent>
        </Card>
        <Card className="bg-purple-50 border-purple-100">
          <CardContent className="pt-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-purple-600">Total Leads</p>
                <p className="text-2xl font-bold text-purple-700">{totalLeads}</p>
              </div>
              <div className="p-2 bg-purple-100 rounded-full">
                <MapPin className="h-5 w-5 text-purple-600" />
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>All Jobs</CardTitle>
          <CardDescription>Click pause to stop a running job, or restart to re-run a completed job.</CardDescription>
        </CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Job ID</TableHead>
                <TableHead>Keyword</TableHead>
                <TableHead>Location</TableHead>
                <TableHead>Radius</TableHead>
                <TableHead>Progress</TableHead>
                <TableHead>Leads Found</TableHead>
                <TableHead>Date</TableHead>
                <TableHead className="text-right">Actions</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {jobs.length === 0 && !loading ? (
                <TableRow>
                  <TableCell colSpan={8} className="text-center py-12 text-zinc-500">
                    <div className="flex flex-col items-center gap-2">
                      <Search className="h-8 w-8 text-zinc-300" />
                      <p>No jobs yet. Create your first scraping job!</p>
                      <Button asChild size="sm" className="mt-2">
                        <Link href="/jobs/new">
                          <PlusCircle className="mr-2 h-4 w-4" />
                          Create Job
                        </Link>
                      </Button>
                    </div>
                  </TableCell>
                </TableRow>
              ) : jobs.map((job) => {
                const progress = job.total_tasks > 0 ? Math.round((job.completed_tasks / job.total_tasks) * 100) : 0
                const isLoading = actionLoading === job.job_id
                
                return (
                  <TableRow key={job.job_id} className={isLoading ? "opacity-50" : ""}>
                    <TableCell className="font-mono text-sm font-medium">{job.job_id}</TableCell>
                    <TableCell>
                      <span className="font-medium">{job.keyword}</span>
                    </TableCell>
                    <TableCell>
                      <div className="flex items-center gap-1">
                        <MapPin className="h-3 w-3 text-zinc-400" />
                        {job.location}
                      </div>
                    </TableCell>
                    <TableCell>{job.radius}km</TableCell>
                    <TableCell>
                      <div className="space-y-1">
                        {getStatusBadge(job.status)}
                        {(job.status === "running" || job.status === "paused") && job.total_tasks > 0 && (
                          <div className="mt-2">
                            <div className="flex items-center gap-2">
                              <div className="flex-1 h-2 bg-zinc-100 rounded-full overflow-hidden">
                                <div 
                                  className={`h-full transition-all duration-500 ${job.status === "paused" ? "bg-amber-500" : "bg-blue-500"}`}
                                  style={{ width: `${progress}%` }}
                                />
                              </div>
                              <span className="text-xs text-zinc-500 w-10">{progress}%</span>
                            </div>
                            <p className="text-xs text-zinc-400 mt-0.5">{job.completed_tasks} of {job.total_tasks} tasks</p>
                          </div>
                        )}
                      </div>
                    </TableCell>
                    <TableCell>
                      <span className={`font-bold ${job.leads_found > 0 ? 'text-emerald-600' : 'text-zinc-300'}`}>
                        {job.leads_found || 0}
                      </span>
                    </TableCell>
                    <TableCell className="text-sm text-zinc-500">
                      {job.created_at ? new Date(job.created_at).toLocaleDateString() : '-'}
                    </TableCell>
                    <TableCell className="text-right">
                      <div className="flex justify-end gap-1">
                        {job.status === "running" ? (
                          <Button 
                            variant="outline" 
                            size="icon" 
                            title="Pause Job"
                            onClick={() => handlePause(job.job_id)}
                            disabled={isLoading}
                          >
                            <Pause className="h-4 w-4" />
                          </Button>
                        ) : job.status === "paused" ? (
                          <Button 
                            variant="outline" 
                            size="icon" 
                            title="Resume Job"
                            onClick={() => handleResume(job.job_id)}
                            disabled={isLoading}
                            className="text-emerald-600 hover:text-emerald-700"
                          >
                            <Play className="h-4 w-4" />
                          </Button>
                        ) : (
                          <Button 
                            variant="outline" 
                            size="icon" 
                            title="Restart Job"
                            onClick={() => handleRestart(job.job_id)}
                            disabled={isLoading}
                          >
                            <RefreshCw className="h-4 w-4" />
                          </Button>
                        )}
                        <Button 
                          variant="outline" 
                          size="icon" 
                          className="text-red-500 hover:text-red-600 hover:bg-red-50" 
                          title="Delete Job"
                          onClick={() => handleDelete(job.job_id)}
                          disabled={isLoading}
                        >
                          <Trash2 className="h-4 w-4" />
                        </Button>
                      </div>
                    </TableCell>
                  </TableRow>
                )
              })}
            </TableBody>
          </Table>
        </CardContent>
      </Card>
    </div>
  )
}
