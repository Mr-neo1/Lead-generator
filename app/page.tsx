"use client"

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Activity, Briefcase, CheckCircle, Phone, Star, TrendingUp, Users, Globe } from "lucide-react"
import { useEffect, useState } from "react"
import { API_URL } from "@/lib/config"

interface Stats {
  totalBusinesses: number
  qualifiedLeads: number
  noWebsiteLeads: number
  activeJobs: number
  completedJobs: number
}

interface AdvancedStats {
  leadTypeDistribution: {
    NO_WEBSITE: number
    WEBSITE_REDESIGN: number
    NORMAL: number
  }
  scoreDistribution: { score: number; count: number }[]
  topCategories: { category: string; count: number }[]
  topLeads: {
    id: number
    name: string
    category: string
    phone: string
    rating: number
    type: string
    score: number
  }[]
  recentJobs: {
    job_id: string
    keyword: string
    location: string
    status: string
    progress: number
    leads_found: number
  }[]
  averageRating: number
}

export default function DashboardPage() {
  const [stats, setStats] = useState<Stats>({ totalBusinesses: 0, qualifiedLeads: 0, noWebsiteLeads: 0, activeJobs: 0, completedJobs: 0 })
  const [advancedStats, setAdvancedStats] = useState<AdvancedStats | null>(null)

  useEffect(() => {
    fetch(`${API_URL}/api/stats`).then(r => r.json()).then(setStats).catch(console.error)
    fetch(`${API_URL}/api/stats/advanced`).then(r => r.json()).then(setAdvancedStats).catch(console.error)
  }, [])

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h2 className="text-3xl font-bold tracking-tight">Dashboard</h2>
      </div>

      {/* Main Stats Cards */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-5">
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
        <Card className="border-red-200 bg-red-50/50">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium text-red-700">No Website</CardTitle>
            <Globe className="h-4 w-4 text-red-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-red-700">{stats.noWebsiteLeads.toLocaleString()}</div>
            <p className="text-xs text-red-600">High priority leads</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Active Jobs</CardTitle>
            <Activity className="h-4 w-4 text-blue-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats.activeJobs}</div>
            <p className="text-xs text-zinc-500">Currently running</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Completed Jobs</CardTitle>
            <CheckCircle className="h-4 w-4 text-emerald-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-emerald-600">{stats.completedJobs}</div>
            <p className="text-xs text-zinc-500">Successfully finished</p>
          </CardContent>
        </Card>
      </div>

      {/* Lead Type Distribution & Score Distribution */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Lead Type Breakdown</CardTitle>
          </CardHeader>
          <CardContent>
            {advancedStats ? (
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <div className="w-3 h-3 rounded-full bg-red-500" />
                    <span className="text-sm">No Website</span>
                  </div>
                  <span className="font-bold text-red-600">{advancedStats.leadTypeDistribution.NO_WEBSITE}</span>
                </div>
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <div className="w-3 h-3 rounded-full bg-amber-500" />
                    <span className="text-sm">Needs Redesign</span>
                  </div>
                  <span className="font-bold text-amber-600">{advancedStats.leadTypeDistribution.WEBSITE_REDESIGN}</span>
                </div>
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <div className="w-3 h-3 rounded-full bg-zinc-400" />
                    <span className="text-sm">Normal</span>
                  </div>
                  <span className="font-bold text-zinc-600">{advancedStats.leadTypeDistribution.NORMAL}</span>
                </div>
                {/* Visual bar */}
                <div className="h-4 rounded-full overflow-hidden flex bg-zinc-100 mt-2">
                  {(() => {
                    const total = advancedStats.leadTypeDistribution.NO_WEBSITE + advancedStats.leadTypeDistribution.WEBSITE_REDESIGN + advancedStats.leadTypeDistribution.NORMAL
                    if (total === 0) return <div className="w-full bg-zinc-200" />
                    return (
                      <>
                        <div className="bg-red-500 h-full" style={{ width: `${(advancedStats.leadTypeDistribution.NO_WEBSITE / total) * 100}%` }} />
                        <div className="bg-amber-500 h-full" style={{ width: `${(advancedStats.leadTypeDistribution.WEBSITE_REDESIGN / total) * 100}%` }} />
                        <div className="bg-zinc-400 h-full" style={{ width: `${(advancedStats.leadTypeDistribution.NORMAL / total) * 100}%` }} />
                      </>
                    )
                  })()}
                </div>
              </div>
            ) : (
              <div className="h-32 flex items-center justify-center text-zinc-400">Loading...</div>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="text-base">Score Distribution</CardTitle>
          </CardHeader>
          <CardContent>
            {advancedStats ? (
              <div className="flex items-end justify-between h-32 gap-1">
                {advancedStats.scoreDistribution.map((item) => {
                  const maxCount = Math.max(...advancedStats.scoreDistribution.map(s => s.count), 1)
                  const height = (item.count / maxCount) * 100
                  return (
                    <div key={item.score} className="flex-1 flex flex-col items-center gap-1">
                      <div 
                        className={`w-full rounded-t transition-all ${item.score >= 6 ? 'bg-emerald-500' : item.score >= 4 ? 'bg-amber-500' : 'bg-zinc-300'}`}
                        style={{ height: `${Math.max(height, 4)}%` }}
                        title={`Score ${item.score}: ${item.count} leads`}
                      />
                      <span className="text-xs text-zinc-500">{item.score}</span>
                    </div>
                  )
                })}
              </div>
            ) : (
              <div className="h-32 flex items-center justify-center text-zinc-400">Loading...</div>
            )}
            <p className="text-xs text-zinc-500 mt-2 text-center">Lead scores from 0-8</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between">
            <CardTitle className="text-base">Top Categories</CardTitle>
            <TrendingUp className="h-4 w-4 text-zinc-400" />
          </CardHeader>
          <CardContent>
            {advancedStats?.topCategories?.length ? (
              <div className="space-y-2">
                {advancedStats.topCategories.slice(0, 5).map((cat, i) => (
                  <div key={cat.category} className="flex items-center justify-between">
                    <span className="text-sm truncate flex-1">{cat.category}</span>
                    <Badge variant="outline" className="ml-2">{cat.count}</Badge>
                  </div>
                ))}
              </div>
            ) : (
              <div className="h-32 flex items-center justify-center text-zinc-400">No data yet</div>
            )}
          </CardContent>
        </Card>
      </div>

      {/* High Value Leads & Recent Jobs */}
      <div className="grid gap-4 md:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Star className="h-4 w-4 text-amber-500" />
              High Value Leads
            </CardTitle>
          </CardHeader>
          <CardContent>
            {advancedStats?.topLeads?.length ? (
              <div className="space-y-4">
                {advancedStats.topLeads.map((lead) => (
                  <div key={lead.id} className="flex items-center justify-between p-3 bg-zinc-50 rounded-lg">
                    <div className="flex-1">
                      <p className="font-medium">{lead.name}</p>
                      <div className="flex items-center gap-2 mt-1">
                        <span className="text-xs text-zinc-500">{lead.category}</span>
                        {lead.phone && (
                          <span className="text-xs text-zinc-500 flex items-center gap-1">
                            <Phone className="h-3 w-3" />
                            {lead.phone}
                          </span>
                        )}
                      </div>
                    </div>
                    <div className="flex items-center gap-2">
                      <Badge variant={lead.type === "NO_WEBSITE" ? "destructive" : "secondary"}>
                        {lead.type.replace("_", " ")}
                      </Badge>
                      <span className="font-bold text-emerald-600">{lead.score}/8</span>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="h-48 flex items-center justify-center text-zinc-400">
                No high-value leads yet. Start a scraping job!
              </div>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Recent Jobs</CardTitle>
          </CardHeader>
          <CardContent>
            {advancedStats?.recentJobs?.length ? (
              <div className="space-y-4">
                {advancedStats.recentJobs.map((job) => (
                  <div key={job.job_id} className="p-3 bg-zinc-50 rounded-lg">
                    <div className="flex items-center justify-between mb-2">
                      <span className="font-medium">{job.keyword} in {job.location}</span>
                      <Badge variant={job.status === 'completed' ? 'default' : job.status === 'running' ? 'secondary' : 'outline'}>
                        {job.status}
                      </Badge>
                    </div>
                    <div className="flex items-center justify-between text-sm">
                      <div className="flex items-center gap-2 flex-1">
                        <div className="flex-1 h-2 bg-zinc-200 rounded-full overflow-hidden">
                          <div 
                            className={`h-full transition-all ${job.status === 'completed' ? 'bg-emerald-500' : 'bg-blue-500'}`}
                            style={{ width: `${job.progress}%` }}
                          />
                        </div>
                        <span className="text-xs text-zinc-500 w-12">{job.progress}%</span>
                      </div>
                      <span className="text-emerald-600 font-medium ml-4">{job.leads_found} leads</span>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="h-48 flex items-center justify-center text-zinc-400">
                No jobs yet. Create one to get started!
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Average Rating Card */}
      {advancedStats && (
        <Card className="max-w-xs">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Average Lead Rating</CardTitle>
            <Star className="h-4 w-4 text-amber-400 fill-amber-400" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{advancedStats.averageRating}</div>
            <p className="text-xs text-zinc-500">Across all businesses with ratings</p>
          </CardContent>
        </Card>
      )}
    </div>
  )
}
