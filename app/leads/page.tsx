"use client"

import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import { Badge } from "@/components/ui/badge"
import { Input } from "@/components/ui/input"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Download, Filter, Search } from "lucide-react"
import { useState, useEffect } from "react"
import { API_URL } from "@/lib/config"

interface Lead {
  id: number
  name: string
  phone: string | null
  website: string | null
  rating: number | null
  reviews: number | null
  category: string | null
  address: string | null
  maps_url: string | null
  type: string
  score: number
}

export default function LeadsPage() {
  const [search, setSearch] = useState("")
  const [filterType, setFilterType] = useState("ALL")
  const [leads, setLeads] = useState<Lead[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetch(`${API_URL}/api/leads`)
      .then(r => r.json())
      .then(data => {
        setLeads(data)
        setLoading(false)
      })
      .catch(err => {
        console.error(err)
        setLoading(false)
      })
  }, [])

  const filteredLeads = leads.filter(lead => {
    const matchesSearch = lead.name.toLowerCase().includes(search.toLowerCase()) || (lead.category?.toLowerCase().includes(search.toLowerCase()) ?? false)
    const matchesType = filterType === "ALL" || lead.type === filterType
    return matchesSearch && matchesType
  })

  const handleExport = () => {
    const params = new URLSearchParams()
    if (filterType !== "ALL") params.append("lead_type", filterType)
    window.open(`${API_URL}/api/leads/export?${params.toString()}`, '_blank')
  }

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h2 className="text-3xl font-bold tracking-tight">Leads Database</h2>
          <p className="text-zinc-500 mt-1">View, filter, and export qualified leads.</p>
        </div>
        <Button variant="outline" onClick={handleExport}>
          <Download className="mr-2 h-4 w-4" />
          Export CSV
        </Button>
      </div>

      <Card>
        <CardHeader className="pb-4">
          <div className="flex flex-col md:flex-row gap-4 items-center justify-between">
            <div className="relative w-full md:w-96">
              <Search className="absolute left-3 top-2.5 h-4 w-4 text-zinc-500" />
              <Input
                placeholder="Search businesses..."
                className="pl-9"
                value={search}
                onChange={(e) => setSearch(e.target.value)}
              />
            </div>
            <div className="flex items-center gap-2 w-full md:w-auto">
              <Filter className="h-4 w-4 text-zinc-500" />
              <Select value={filterType} onValueChange={setFilterType}>
                <SelectTrigger className="w-[180px]">
                  <SelectValue placeholder="Filter by type" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="ALL">All Leads</SelectItem>
                  <SelectItem value="NO_WEBSITE">No Website (High Priority)</SelectItem>
                  <SelectItem value="WEBSITE_REDESIGN">Needs Redesign</SelectItem>
                  <SelectItem value="NORMAL">Normal</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Business</TableHead>
                <TableHead>Category</TableHead>
                <TableHead>Rating</TableHead>
                <TableHead>Lead Type</TableHead>
                <TableHead>Score</TableHead>
                <TableHead className="text-right">Actions</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {filteredLeads.map((lead) => (
                <TableRow key={lead.id}>
                  <TableCell>
                    <div className="font-medium">{lead.name}</div>
                    <div className="text-xs text-zinc-500">{lead.phone}</div>
                  </TableCell>
                  <TableCell>{lead.category}</TableCell>
                  <TableCell>
                    <div className="flex items-center gap-1">
                      <span className="font-medium">{lead.rating}</span>
                      <span className="text-xs text-zinc-500">({lead.reviews})</span>
                    </div>
                  </TableCell>
                  <TableCell>
                    <Badge variant={lead.type === "NO_WEBSITE" ? "destructive" : lead.type === "WEBSITE_REDESIGN" ? "secondary" : "outline"}>
                      {lead.type.replace("_", " ")}
                    </Badge>
                  </TableCell>
                  <TableCell>
                    <div className={`font-bold ${lead.score >= 6 ? 'text-emerald-600' : lead.score >= 4 ? 'text-amber-600' : 'text-zinc-500'}`}>
                      {lead.score}/8
                    </div>
                  </TableCell>
                  <TableCell className="text-right">
                    <Button variant="outline" size="sm">Details</Button>
                  </TableCell>
                </TableRow>
              ))}
              {filteredLeads.length === 0 && (
                <TableRow>
                  <TableCell colSpan={6} className="text-center py-8 text-zinc-500">
                    No leads found matching your criteria.
                  </TableCell>
                </TableRow>
              )}
            </TableBody>
          </Table>
        </CardContent>
      </Card>
    </div>
  )
}
