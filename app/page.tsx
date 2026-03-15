"use client"

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Skeleton } from "@/components/ui/skeleton"
import { Activity, Briefcase, CheckCircle, Phone, Star, TrendingUp, Users, Globe, RefreshCw } from "lucide-react"
import { Button } from "@/components/ui/button"
import { useStats, useAdvancedStats } from "@/hooks/use-api"
import { toast } from "sonner"

interface ScoreItem {
  score: number
  count: number
}

interface TopCategory {
  category: string
  count: number
}

interface TopLead {
  id: number
  name: string
  category: string
  phone: string
  rating: number
  type: string
  score: number
}

interface RecentJob {
  job_id: string
  keyword: string
  location: string
  status: string
  progress: number
  leads_found: number
}

export default function DashboardPage() {
  const { stats, isLoading: statsLoading, isError: statsError, refresh: refreshStats } = useStats()
  const { advancedStats, isLoading: advancedLoading, isError: advancedError, refresh: refreshAdvanced } = useAdvancedStats()

  const handleRefresh = () => {
    refreshStats()
    refreshAdvanced()
    toast.success("Dashboard refreshed")
  }

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h2 className="text-3xl font-bold tracking-tight">Dashboard</h2>
        <Button variant="outline" size="sm" onClick={handleRefresh} className="gap-2">
          <RefreshCw className="h-4 w-4" />
          Refresh
        </Button>
      </div>

      {/* Error States */}
      {(statsError || advancedError) && (
        <div className="p-4 rounded-lg bg-red-50 dark:bg-red-950 text-red-600 dark:text-red-400">
          Failed to load dashboard data. Please check your connection to the backend.
        </div>
      )}

      {/* Main Stats Cards */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-5">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Businesses</CardTitle>
            <Briefcase className="h-4 w-4 text-zinc-500" />
          </CardHeader>
          <CardContent>
            {statsLoading ? (
              <Skeleton className="h-8 w-20" />
            ) : (
              <>
                <div className="text-2xl font-bold">{(stats?.totalBusinesses || 0).toLocaleString()}</div>
                <p className="text-xs text-zinc-500 dark:text-zinc-400">From scraped data</p>
              </>
            )}
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Qualified Leads</CardTitle>
            <Users className="h-4 w-4 text-zinc-500" />
          </CardHeader>
          <CardContent>
            {statsLoading ? (
              <Skeleton className="h-8 w-20" />
            ) : (
              <>
                <div className="text-2xl font-bold">{(stats?.qualifiedLeads || 0).toLocaleString()}</div>
                <p className="text-xs text-zinc-500 dark:text-zinc-400">Score ≥ 5</p>
              </>
            )}
          </CardContent>
        </Card>
        <Card className="border-red-200 dark:border-red-800 bg-red-50/50 dark:bg-red-950/30">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium text-red-700 dark:text-red-400">No Website</CardTitle>
            <Globe className="h-4 w-4 text-red-500" />
          </CardHeader>
          <CardContent>
            {statsLoading ? (
              <Skeleton className="h-8 w-20" />
            ) : (
              <>
                <div className="text-2xl font-bold text-red-700 dark:text-red-400">{(stats?.noWebsiteLeads || 0).toLocaleString()}</div>
                <p className="text-xs text-red-600 dark:text-red-500">High priority leads</p>
              </>
            )}
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Active Jobs</CardTitle>
            <Activity className="h-4 w-4 text-blue-500" />
          </CardHeader>
          <CardContent>
            {statsLoading ? (
              <Skeleton className="h-8 w-20" />
            ) : (
              <>
                <div className="text-2xl font-bold">{stats?.activeJobs || 0}</div>
                <p className="text-xs text-zinc-500 dark:text-zinc-400">Currently running</p>
              </>
            )}
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Completed Jobs</CardTitle>
            <CheckCircle className="h-4 w-4 text-emerald-500" />
          </CardHeader>
          <CardContent>
            {statsLoading ? (
              <Skeleton className="h-8 w-20" />
            ) : (
              <>
                <div className="text-2xl font-bold text-emerald-600">{stats?.completedJobs || 0}</div>
                <p className="text-xs text-zinc-500 dark:text-zinc-400">Successfully finished</p>
              </>
            )}
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
              <div className="h-32 flex items-center justify-center text-zinc-400 dark:text-zinc-500">Loading...</div>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="text-base">Score Distribution</CardTitle>
          </CardHeader>
          <CardContent>
            {advancedLoading ? (
              <div className="flex items-end justify-between h-32 gap-1">
                {[...Array(9)].map((_, i) => (
                  <Skeleton key={i} className="flex-1 h-16" />
                ))}
              </div>
            ) : advancedStats ? (
              <div className="flex items-end justify-between h-32 gap-1">
                {advancedStats.scoreDistribution.map((item: ScoreItem) => {
                  const maxCount = Math.max(...advancedStats.scoreDistribution.map((s: ScoreItem) => s.count), 1)
                  const height = (item.count / maxCount) * 100
                  return (
                    <div key={item.score} className="flex-1 flex flex-col items-center gap-1">
                      <div 
                        className={`w-full rounded-t transition-all ${item.score >= 6 ? 'bg-emerald-500' : item.score >= 4 ? 'bg-amber-500' : 'bg-zinc-300 dark:bg-zinc-600'}`}
                        style={{ height: `${Math.max(height, 4)}%` }}
                        title={`Score ${item.score}: ${item.count} leads`}
                      />
                      <span className="text-xs text-zinc-500 dark:text-zinc-400">{item.score}</span>
                    </div>
                  )
                })}
              </div>
            ) : (
              <div className="h-32 flex items-center justify-center text-zinc-400 dark:text-zinc-500">Loading...</div>
            )}
            <p className="text-xs text-zinc-500 dark:text-zinc-400 mt-2 text-center">Lead scores from 0-8</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between">
            <CardTitle className="text-base">Top Categories</CardTitle>
            <TrendingUp className="h-4 w-4 text-zinc-400" />
          </CardHeader>
          <CardContent>
            {advancedLoading ? (
              <div className="space-y-2">
                {[...Array(5)].map((_, i) => (
                  <Skeleton key={i} className="h-6 w-full" />
                ))}
              </div>
            ) : advancedStats?.topCategories?.length ? (
              <div className="space-y-2">
                {advancedStats.topCategories.slice(0, 5).map((cat: TopCategory) => (
                  <div key={cat.category} className="flex items-center justify-between">
                    <span className="text-sm truncate flex-1">{cat.category}</span>
                    <Badge variant="outline" className="ml-2">{cat.count}</Badge>
                  </div>
                ))}
              </div>
            ) : (
              <div className="h-32 flex items-center justify-center text-zinc-400 dark:text-zinc-500">No data yet</div>
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
            {advancedLoading ? (
              <div className="space-y-4">
                {[...Array(3)].map((_, i) => (
                  <Skeleton key={i} className="h-20 w-full" />
                ))}
              </div>
            ) : advancedStats?.topLeads?.length ? (
              <div className="space-y-4">
                {advancedStats.topLeads.map((lead: TopLead) => (
                  <div key={lead.id} className="flex items-center justify-between p-3 bg-zinc-50 dark:bg-zinc-800 rounded-lg">
                    <div className="flex-1">
                      <p className="font-medium">{lead.name}</p>
                      <div className="flex items-center gap-2 mt-1">
                        <span className="text-xs text-zinc-500 dark:text-zinc-400">{lead.category}</span>
                        {lead.phone && (
                          <span className="text-xs text-zinc-500 dark:text-zinc-400 flex items-center gap-1">
                            <Phone className="h-3 w-3" />
                            {lead.phone}
                          </span>
                        )}
                      </div>
                    </div>
                    <div className="flex items-center gap-2">
                      <Badge variant={lead.type === "NO_WEBSITE" ? "destructive" : "secondary"}>
                        {lead.type.replaceAll("_", " ")}
                      </Badge>
                      <span className="font-bold text-emerald-600">{lead.score}/8</span>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="h-48 flex items-center justify-center text-zinc-400 dark:text-zinc-500">
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
            {advancedLoading ? (
              <div className="space-y-4">
                {[...Array(3)].map((_, i) => (
                  <Skeleton key={i} className="h-20 w-full" />
                ))}
              </div>
            ) : advancedStats?.recentJobs?.length ? (
              <div className="space-y-4">
                {advancedStats.recentJobs.map((job: RecentJob) => (
                  <div key={job.job_id} className="p-3 bg-zinc-50 dark:bg-zinc-800 rounded-lg">
                    <div className="flex items-center justify-between mb-2">
                      <span className="font-medium">{job.keyword} in {job.location}</span>
                      <Badge variant={job.status === 'completed' ? 'default' : job.status === 'running' ? 'secondary' : 'outline'}>
                        {job.status}
                      </Badge>
                    </div>
                    <div className="flex items-center justify-between text-sm">
                      <div className="flex items-center gap-2 flex-1">
                        <div className="flex-1 h-2 bg-zinc-200 dark:bg-zinc-700 rounded-full overflow-hidden">
                          <div 
                            className={`h-full transition-all ${job.status === 'completed' ? 'bg-emerald-500' : 'bg-blue-500'}`}
                            style={{ width: `${job.progress}%` }}
                          />
                        </div>
                        <span className="text-xs text-zinc-500 dark:text-zinc-400 w-12">{job.progress}%</span>
                      </div>
                      <span className="text-emerald-600 font-medium ml-4">{job.leads_found} leads</span>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="h-48 flex items-center justify-center text-zinc-400 dark:text-zinc-500">
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
            <p className="text-xs text-zinc-500 dark:text-zinc-400">Across all businesses with ratings</p>
          </CardContent>
        </Card>
      )}
    </div>
  )
}
