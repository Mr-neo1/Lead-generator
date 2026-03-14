"use client"

import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import { Badge } from "@/components/ui/badge"
import { Skeleton } from "@/components/ui/skeleton"
import { AlertDialog, AlertDialogAction, AlertDialogCancel, AlertDialogContent, AlertDialogDescription, AlertDialogFooter, AlertDialogHeader, AlertDialogTitle, AlertDialogTrigger } from "@/components/ui/alert-dialog"
import { Pagination } from "@/components/pagination"
import { PlusCircle, Play, Pause, XCircle, Trash2, RefreshCw, MapPin, Search } from "lucide-react"
import Link from "next/link"
import { useState } from "react"
import { useJobs, deleteJob, cancelJob, restartJob } from "@/hooks/use-api"
import { toast } from "sonner"
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
  failed_tasks?: number
  leads_found: number
  created_at: string | null
  error_message?: string
}

export default function JobsPage() {
  const [page, setPage] = useState(1)
  const [actionLoading, setActionLoading] = useState<string | null>(null)
  const pageSize = 20

  const { jobs, pagination, isLoading, isError: error, refresh: mutate } = useJobs({ page, pageSize })
  
  const totalPages = pagination.totalPages

  const handlePause = async (jobId: string) => {
    setActionLoading(jobId)
    try {
      await fetch(`${API_URL}/api/jobs/${jobId}/pause`, { method: 'POST' })
      toast.success("Job paused")
      mutate()
    } catch {
      toast.error("Failed to pause job")
    }
    setActionLoading(null)
  }

  const handleResume = async (jobId: string) => {
    setActionLoading(jobId)
    try {
      await fetch(`${API_URL}/api/jobs/${jobId}/resume`, { method: 'POST' })
      toast.success("Job resumed")
      mutate()
    } catch {
      toast.error("Failed to resume job")
    }
    setActionLoading(null)
  }

  const handleRestart = async (jobId: string) => {
    setActionLoading(jobId)
    try {
      await restartJob(jobId)
      toast.success("Job restarted")
      mutate()
    } catch {
      toast.error("Failed to restart job")
    }
    setActionLoading(null)
  }

  const handleCancel = async (jobId: string) => {
    setActionLoading(jobId)
    try {
      await cancelJob(jobId)
      toast.success("Job cancelled")
      mutate()
    } catch {
      toast.error("Failed to cancel job")
    }
    setActionLoading(null)
  }

  const handleDelete = async (jobId: string) => {
    setActionLoading(jobId)
    try {
      await deleteJob(jobId)
      toast.success("Job deleted")
      mutate()
    } catch {
      toast.error("Failed to delete job")
    }
    setActionLoading(null)
  }

  const getStatusBadge = (status: string) => {
    const colors: Record<string, string> = {
      completed: "bg-emerald-100 dark:bg-emerald-900 text-emerald-700 dark:text-emerald-300 border-emerald-200 dark:border-emerald-800",
      running: "bg-blue-100 dark:bg-blue-900 text-blue-700 dark:text-blue-300 border-blue-200 dark:border-blue-800 animate-pulse",
      paused: "bg-amber-100 dark:bg-amber-900 text-amber-700 dark:text-amber-300 border-amber-200 dark:border-amber-800",
      failed: "bg-red-100 dark:bg-red-900 text-red-700 dark:text-red-300 border-red-200 dark:border-red-800",
      cancelled: "bg-zinc-100 dark:bg-zinc-800 text-zinc-600 dark:text-zinc-400 border-zinc-200 dark:border-zinc-700",
      pending: "bg-zinc-100 dark:bg-zinc-800 text-zinc-600 dark:text-zinc-400 border-zinc-200 dark:border-zinc-700"
    }
    return (
      <Badge variant="outline" className={colors[status] || ""}>
        {status}
      </Badge>
    )
  }

  const runningJobs = (jobs as Job[]).filter((j: Job) => j.status === "running").length
  const completedJobs = (jobs as Job[]).filter((j: Job) => j.status === "completed").length
  const totalLeads = (jobs as Job[]).reduce((sum: number, j: Job) => sum + (j.leads_found || 0), 0)
  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h2 className="text-3xl font-bold tracking-tight">Scraping Jobs</h2>
          <p className="text-zinc-500 dark:text-zinc-400 mt-1">Manage your automated lead generation jobs.</p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" onClick={() => mutate()} disabled={isLoading}>
            <RefreshCw className={`mr-2 h-4 w-4 ${isLoading ? 'animate-spin' : ''}`} />
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

      {error && (
        <div className="p-4 rounded-lg bg-red-50 dark:bg-red-950 text-red-600 dark:text-red-400">
          Failed to load jobs. Please check your connection to the backend.
        </div>
      )}

      {/* Quick Stats */}
      <div className="grid grid-cols-3 gap-4">
        <Card className="bg-blue-50 dark:bg-blue-950 border-blue-100 dark:border-blue-900">
          <CardContent className="pt-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-blue-600 dark:text-blue-400">Running</p>
                {isLoading ? (
                  <Skeleton className="h-8 w-12" />
                ) : (
                  <p className="text-2xl font-bold text-blue-700 dark:text-blue-300">{runningJobs}</p>
                )}
              </div>
              <div className="p-2 bg-blue-100 dark:bg-blue-900 rounded-full">
                <RefreshCw className={`h-5 w-5 text-blue-600 dark:text-blue-400 ${runningJobs > 0 ? 'animate-spin' : ''}`} />
              </div>
            </div>
          </CardContent>
        </Card>
        <Card className="bg-emerald-50 dark:bg-emerald-950 border-emerald-100 dark:border-emerald-900">
          <CardContent className="pt-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-emerald-600 dark:text-emerald-400">Completed</p>
                {isLoading ? (
                  <Skeleton className="h-8 w-12" />
                ) : (
                  <p className="text-2xl font-bold text-emerald-700 dark:text-emerald-300">{completedJobs}</p>
                )}
              </div>
              <div className="p-2 bg-emerald-100 dark:bg-emerald-900 rounded-full">
                <Search className="h-5 w-5 text-emerald-600 dark:text-emerald-400" />
              </div>
            </div>
          </CardContent>
        </Card>
        <Card className="bg-purple-50 dark:bg-purple-950 border-purple-100 dark:border-purple-900">
          <CardContent className="pt-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-purple-600 dark:text-purple-400">Total Leads</p>
                {isLoading ? (
                  <Skeleton className="h-8 w-16" />
                ) : (
                  <p className="text-2xl font-bold text-purple-700 dark:text-purple-300">{totalLeads}</p>
                )}
              </div>
              <div className="p-2 bg-purple-100 dark:bg-purple-900 rounded-full">
                <MapPin className="h-5 w-5 text-purple-600 dark:text-purple-400" />
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
              {isLoading ? (
                [...Array(5)].map((_, i) => (
                  <TableRow key={i}>
                    {[...Array(8)].map((_, j) => (
                      <TableCell key={j}><Skeleton className="h-6 w-full" /></TableCell>
                    ))}
                  </TableRow>
                ))
              ) : jobs.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={8} className="text-center py-12 text-zinc-500 dark:text-zinc-400">
                    <div className="flex flex-col items-center gap-2">
                      <Search className="h-8 w-8 text-zinc-300 dark:text-zinc-600" />
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
              ) : (jobs as Job[]).map((job: Job) => {
                const progress = job.total_tasks > 0 ? Math.round((job.completed_tasks / job.total_tasks) * 100) : 0
                const isActionLoading = actionLoading === job.job_id
                
                return (
                  <TableRow key={job.job_id} className={isActionLoading ? "opacity-50" : ""}>
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
                        {job.error_message && (
                          <p className="text-xs text-red-500 dark:text-red-400 mt-1" title={job.error_message}>
                            Error: {job.error_message.slice(0, 30)}...
                          </p>
                        )}
                        {(job.status === "running" || job.status === "paused") && job.total_tasks > 0 && (
                          <div className="mt-2">
                            <div className="flex items-center gap-2">
                              <div className="flex-1 h-2 bg-zinc-100 dark:bg-zinc-800 rounded-full overflow-hidden">
                                <div 
                                  className={`h-full transition-all duration-500 ${job.status === "paused" ? "bg-amber-500" : "bg-blue-500"}`}
                                  style={{ width: `${progress}%` }}
                                />
                              </div>
                              <span className="text-xs text-zinc-500 dark:text-zinc-400 w-10">{progress}%</span>
                            </div>
                            <p className="text-xs text-zinc-400 dark:text-zinc-500 mt-0.5">
                              {job.completed_tasks} of {job.total_tasks} tasks
                              {job.failed_tasks && job.failed_tasks > 0 && (
                                <span className="text-red-500"> ({job.failed_tasks} failed)</span>
                              )}
                            </p>
                          </div>
                        )}
                      </div>
                    </TableCell>
                    <TableCell>
                      <span className={`font-bold ${job.leads_found > 0 ? 'text-emerald-600 dark:text-emerald-400' : 'text-zinc-300 dark:text-zinc-600'}`}>
                        {job.leads_found || 0}
                      </span>
                    </TableCell>
                    <TableCell className="text-sm text-zinc-500 dark:text-zinc-400">
                      {job.created_at ? new Date(job.created_at).toLocaleDateString() : '-'}
                    </TableCell>
                    <TableCell className="text-right">
                      <div className="flex justify-end gap-1">
                        {job.status === "running" ? (
                          <>
                            <Button 
                              variant="outline" 
                              size="icon" 
                              title="Pause Job"
                              onClick={() => handlePause(job.job_id)}
                              disabled={isActionLoading}
                            >
                              <Pause className="h-4 w-4" />
                            </Button>
                            <AlertDialog>
                              <AlertDialogTrigger asChild>
                                <Button 
                                  variant="outline" 
                                  size="icon" 
                                  title="Cancel Job"
                                  className="text-red-500 hover:text-red-600"
                                  disabled={isActionLoading}
                                >
                                  <XCircle className="h-4 w-4" />
                                </Button>
                              </AlertDialogTrigger>
                              <AlertDialogContent>
                                <AlertDialogHeader>
                                  <AlertDialogTitle>Cancel this job?</AlertDialogTitle>
                                  <AlertDialogDescription>
                                    This will stop all pending tasks. Leads already found will be kept.
                                  </AlertDialogDescription>
                                </AlertDialogHeader>
                                <AlertDialogFooter>
                                  <AlertDialogCancel>Keep Running</AlertDialogCancel>
                                  <AlertDialogAction onClick={() => handleCancel(job.job_id)} className="bg-red-600 hover:bg-red-700">
                                    Cancel Job
                                  </AlertDialogAction>
                                </AlertDialogFooter>
                              </AlertDialogContent>
                            </AlertDialog>
                          </>
                        ) : job.status === "paused" ? (
                          <Button 
                            variant="outline" 
                            size="icon" 
                            title="Resume Job"
                            onClick={() => handleResume(job.job_id)}
                            disabled={isActionLoading}
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
                            disabled={isActionLoading}
                          >
                            <RefreshCw className="h-4 w-4" />
                          </Button>
                        )}
                        <AlertDialog>
                          <AlertDialogTrigger asChild>
                            <Button 
                              variant="outline" 
                              size="icon" 
                              className="text-red-500 hover:text-red-600 hover:bg-red-50 dark:hover:bg-red-950" 
                              title="Delete Job"
                              disabled={isActionLoading}
                            >
                              <Trash2 className="h-4 w-4" />
                            </Button>
                          </AlertDialogTrigger>
                          <AlertDialogContent>
                            <AlertDialogHeader>
                              <AlertDialogTitle>Delete job {job.job_id}?</AlertDialogTitle>
                              <AlertDialogDescription>
                                This action cannot be undone. The job and its associated leads will be permanently deleted.
                              </AlertDialogDescription>
                            </AlertDialogHeader>
                            <AlertDialogFooter>
                              <AlertDialogCancel>Cancel</AlertDialogCancel>
                              <AlertDialogAction onClick={() => handleDelete(job.job_id)} className="bg-red-600 hover:bg-red-700">
                                Delete
                              </AlertDialogAction>
                            </AlertDialogFooter>
                          </AlertDialogContent>
                        </AlertDialog>
                      </div>
                    </TableCell>
                  </TableRow>
                )
              })}
            </TableBody>
          </Table>

          {/* Pagination */}
          {totalPages > 1 && (
            <div className="mt-4 flex justify-center">
              <Pagination
                page={page}
                totalPages={totalPages}
                onPageChange={setPage}
              />
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  )
}
