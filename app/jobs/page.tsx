"use client"

import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import { Badge } from "@/components/ui/badge"
import { PlusCircle, Play, Pause, Trash2 } from "lucide-react"
import Link from "next/link"
import { useEffect, useState } from "react"
import { API_URL } from "@/lib/config"

interface Job {
  job_id: string
  keyword: string
  location: string
  radius: number
  grid_size: string
  status: string
  created_at: string | null
}

export default function JobsPage() {
  const [jobs, setJobs] = useState<Job[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
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
  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h2 className="text-3xl font-bold tracking-tight">Scraping Jobs</h2>
          <p className="text-zinc-500 mt-1">Manage your automated lead generation jobs.</p>
        </div>
        <Button asChild>
          <Link href="/jobs/new">
            <PlusCircle className="mr-2 h-4 w-4" />
            New Job
          </Link>
        </Button>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>All Jobs</CardTitle>
        </CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Job ID</TableHead>
                <TableHead>Keyword</TableHead>
                <TableHead>Location</TableHead>
                <TableHead>Radius</TableHead>
                <TableHead>Status</TableHead>
                <TableHead>Leads Found</TableHead>
                <TableHead>Date</TableHead>
                <TableHead className="text-right">Actions</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {jobs.length === 0 && !loading ? (
                <TableRow>
                  <TableCell colSpan={8} className="text-center py-8 text-zinc-500">
                    No jobs yet. Create your first scraping job!
                  </TableCell>
                </TableRow>
              ) : jobs.map((job) => (
                <TableRow key={job.job_id}>
                  <TableCell className="font-medium">{job.job_id}</TableCell>
                  <TableCell>{job.keyword}</TableCell>
                  <TableCell>{job.location}</TableCell>
                  <TableCell>{job.radius}km</TableCell>
                  <TableCell>
                    <Badge variant={job.status === "completed" ? "default" : job.status === "running" ? "secondary" : job.status === "failed" ? "destructive" : "outline"}>
                      {job.status}
                    </Badge>
                  </TableCell>
                  <TableCell>-</TableCell>
                  <TableCell>{job.created_at ? new Date(job.created_at).toLocaleDateString() : '-'}</TableCell>
                  <TableCell className="text-right">
                    <div className="flex justify-end gap-2">
                      {job.status === "running" ? (
                        <Button variant="outline" size="icon" title="Pause">
                          <Pause className="h-4 w-4" />
                        </Button>
                      ) : (
                        <Button variant="outline" size="icon" title="Run">
                          <Play className="h-4 w-4" />
                        </Button>
                      )}
                      <Button variant="outline" size="icon" className="text-red-500 hover:text-red-600" title="Delete">
                        <Trash2 className="h-4 w-4" />
                      </Button>
                    </div>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </CardContent>
      </Card>
    </div>
  )
}
