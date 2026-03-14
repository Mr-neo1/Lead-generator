"use client"

import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import { Badge } from "@/components/ui/badge"
import { Input } from "@/components/ui/input"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Skeleton } from "@/components/ui/skeleton"
import { AlertDialog, AlertDialogAction, AlertDialogCancel, AlertDialogContent, AlertDialogDescription, AlertDialogFooter, AlertDialogHeader, AlertDialogTitle, AlertDialogTrigger } from "@/components/ui/alert-dialog"
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from "@/components/ui/dialog"
import { Label } from "@/components/ui/label"
import { Pagination } from "@/components/pagination"
import { Download, Filter, Search, Trash2, Edit, ExternalLink, RefreshCw, CheckSquare, Square } from "lucide-react"
import { useState, useMemo } from "react"
import { useLeads, deleteLead, updateLead, bulkDeleteLeads, bulkUpdateLeads } from "@/hooks/use-api"
import { toast } from "sonner"
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
  status?: string
  notes?: string
  tags?: string
}

export default function LeadsPage() {
  const [search, setSearch] = useState("")
  const [filterType, setFilterType] = useState("ALL")
  const [filterStatus, setFilterStatus] = useState("ALL")
  const [page, setPage] = useState(1)
  const [selectedLeads, setSelectedLeads] = useState<number[]>([])
  const [editingLead, setEditingLead] = useState<Lead | null>(null)
  const [editForm, setEditForm] = useState({ notes: "", tags: "", status: "" })
  const pageSize = 25

  const { leads, pagination, isLoading, isError: error, refresh: mutate } = useLeads({
    page,
    pageSize,
    leadType: filterType !== "ALL" ? filterType : undefined
  })

  const totalPages = pagination.totalPages
  const totalItems = pagination.total

  // Client-side search filtering
  const filteredLeads = useMemo(() => {
    return leads.filter((lead: Lead) => {
      const matchesSearch = !search || 
        lead.name.toLowerCase().includes(search.toLowerCase()) || 
        (lead.category?.toLowerCase().includes(search.toLowerCase()) ?? false) ||
        (lead.phone?.includes(search) ?? false)
      const matchesStatus = filterStatus === "ALL" || lead.status === filterStatus
      return matchesSearch && matchesStatus
    })
  }, [leads, search, filterStatus])

  const handleExport = () => {
    const params = new URLSearchParams()
    if (filterType !== "ALL") params.append("lead_type", filterType)
    window.open(`${API_URL}/api/leads/export?${params.toString()}`, '_blank')
    toast.success("Export started")
  }

  const handleDelete = async (id: number) => {
    try {
      await deleteLead(id)
      toast.success("Lead deleted successfully")
      mutate()
    } catch {
      toast.error("Failed to delete lead")
    }
  }

  const handleBulkDelete = async () => {
    if (selectedLeads.length === 0) return
    try {
      await bulkDeleteLeads(selectedLeads)
      toast.success(`${selectedLeads.length} leads deleted`)
      setSelectedLeads([])
      mutate()
    } catch {
      toast.error("Failed to delete leads")
    }
  }

  const handleBulkUpdateStatus = async (status: string) => {
    if (selectedLeads.length === 0) return
    try {
      await bulkUpdateLeads(selectedLeads, { status })
      toast.success(`${selectedLeads.length} leads updated to ${status}`)
      setSelectedLeads([])
      mutate()
    } catch {
      toast.error("Failed to update leads")
    }
  }

  const openEditDialog = (lead: Lead) => {
    setEditingLead(lead)
    setEditForm({
      notes: lead.notes || "",
      tags: lead.tags || "",
      status: lead.status || "new"
    })
  }

  const handleSaveEdit = async () => {
    if (!editingLead) return
    try {
      await updateLead(editingLead.id, editForm)
      toast.success("Lead updated successfully")
      setEditingLead(null)
      mutate()
    } catch {
      toast.error("Failed to update lead")
    }
  }

  const toggleSelectLead = (id: number) => {
    setSelectedLeads(prev => 
      prev.includes(id) ? prev.filter(i => i !== id) : [...prev, id]
    )
  }

  const toggleSelectAll = () => {
    if (selectedLeads.length === filteredLeads.length) {
      setSelectedLeads([])
    } else {
      setSelectedLeads(filteredLeads.map((l: Lead) => l.id))
    }
  }

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h2 className="text-3xl font-bold tracking-tight">Leads Database</h2>
          <p className="text-zinc-500 dark:text-zinc-400 mt-1">
            {totalItems.toLocaleString()} leads found. Page {page} of {totalPages}.
          </p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" onClick={() => mutate()}>
            <RefreshCw className="mr-2 h-4 w-4" />
            Refresh
          </Button>
          <Button variant="outline" onClick={handleExport}>
            <Download className="mr-2 h-4 w-4" />
            Export CSV
          </Button>
        </div>
      </div>

      {/* Bulk Actions Bar */}
      {selectedLeads.length > 0 && (
        <Card className="border-blue-200 dark:border-blue-800 bg-blue-50 dark:bg-blue-950">
          <CardContent className="py-3 flex items-center justify-between">
            <span className="font-medium">{selectedLeads.length} leads selected</span>
            <div className="flex gap-2">
              <Select onValueChange={handleBulkUpdateStatus}>
                <SelectTrigger className="w-[150px]">
                  <SelectValue placeholder="Set status..." />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="new">New</SelectItem>
                  <SelectItem value="contacted">Contacted</SelectItem>
                  <SelectItem value="qualified">Qualified</SelectItem>
                  <SelectItem value="converted">Converted</SelectItem>
                  <SelectItem value="lost">Lost</SelectItem>
                </SelectContent>
              </Select>
              <AlertDialog>
                <AlertDialogTrigger asChild>
                  <Button variant="destructive" size="sm">
                    <Trash2 className="mr-2 h-4 w-4" />
                    Delete Selected
                  </Button>
                </AlertDialogTrigger>
                <AlertDialogContent>
                  <AlertDialogHeader>
                    <AlertDialogTitle>Delete {selectedLeads.length} leads?</AlertDialogTitle>
                    <AlertDialogDescription>
                      This action cannot be undone. All selected leads will be permanently deleted.
                    </AlertDialogDescription>
                  </AlertDialogHeader>
                  <AlertDialogFooter>
                    <AlertDialogCancel>Cancel</AlertDialogCancel>
                    <AlertDialogAction onClick={handleBulkDelete} className="bg-red-600 hover:bg-red-700">
                      Delete
                    </AlertDialogAction>
                  </AlertDialogFooter>
                </AlertDialogContent>
              </AlertDialog>
              <Button variant="outline" size="sm" onClick={() => setSelectedLeads([])}>
                Clear Selection
              </Button>
            </div>
          </CardContent>
        </Card>
      )}

      {error && (
        <div className="p-4 rounded-lg bg-red-50 dark:bg-red-950 text-red-600 dark:text-red-400">
          Failed to load leads. Please check your connection to the backend.
        </div>
      )}

      <Card>
        <CardHeader className="pb-4">
          <div className="flex flex-col md:flex-row gap-4 items-center justify-between">
            <div className="relative w-full md:w-96">
              <Search className="absolute left-3 top-2.5 h-4 w-4 text-zinc-500" />
              <Input
                placeholder="Search by name, category, or phone..."
                className="pl-9"
                value={search}
                onChange={(e) => setSearch(e.target.value)}
              />
            </div>
            <div className="flex items-center gap-2 w-full md:w-auto">
              <Filter className="h-4 w-4 text-zinc-500" />
              <Select value={filterType} onValueChange={(v) => { setFilterType(v); setPage(1); }}>
                <SelectTrigger className="w-[180px]">
                  <SelectValue placeholder="Filter by type" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="ALL">All Types</SelectItem>
                  <SelectItem value="NO_WEBSITE">No Website</SelectItem>
                  <SelectItem value="WEBSITE_REDESIGN">Needs Redesign</SelectItem>
                  <SelectItem value="NORMAL">Normal</SelectItem>
                </SelectContent>
              </Select>
              <Select value={filterStatus} onValueChange={setFilterStatus}>
                <SelectTrigger className="w-[150px]">
                  <SelectValue placeholder="Status" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="ALL">All Status</SelectItem>
                  <SelectItem value="new">New</SelectItem>
                  <SelectItem value="contacted">Contacted</SelectItem>
                  <SelectItem value="qualified">Qualified</SelectItem>
                  <SelectItem value="converted">Converted</SelectItem>
                  <SelectItem value="lost">Lost</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead className="w-10">
                  <Button variant="ghost" size="sm" onClick={toggleSelectAll} className="p-0">
                    {selectedLeads.length === filteredLeads.length && filteredLeads.length > 0 ? (
                      <CheckSquare className="h-4 w-4" />
                    ) : (
                      <Square className="h-4 w-4" />
                    )}
                  </Button>
                </TableHead>
                <TableHead>Business</TableHead>
                <TableHead>Category</TableHead>
                <TableHead>Rating</TableHead>
                <TableHead>Lead Type</TableHead>
                <TableHead>Status</TableHead>
                <TableHead>Score</TableHead>
                <TableHead className="text-right">Actions</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {isLoading ? (
                [...Array(10)].map((_, i) => (
                  <TableRow key={i}>
                    {[...Array(8)].map((_, j) => (
                      <TableCell key={j}><Skeleton className="h-6 w-full" /></TableCell>
                    ))}
                  </TableRow>
                ))
              ) : filteredLeads.length > 0 ? (
                filteredLeads.map((lead: Lead) => (
                  <TableRow key={lead.id} className={selectedLeads.includes(lead.id) ? "bg-blue-50 dark:bg-blue-950" : ""}>
                    <TableCell>
                      <Button variant="ghost" size="sm" onClick={() => toggleSelectLead(lead.id)} className="p-0">
                        {selectedLeads.includes(lead.id) ? (
                          <CheckSquare className="h-4 w-4 text-blue-600" />
                        ) : (
                          <Square className="h-4 w-4" />
                        )}
                      </Button>
                    </TableCell>
                    <TableCell>
                      <div className="font-medium">{lead.name}</div>
                      <div className="text-xs text-zinc-500 dark:text-zinc-400">{lead.phone || "No phone"}</div>
                    </TableCell>
                    <TableCell>{lead.category || "-"}</TableCell>
                    <TableCell>
                      {lead.rating ? (
                        <div className="flex items-center gap-1">
                          <span className="font-medium">{lead.rating}</span>
                          <span className="text-xs text-zinc-500 dark:text-zinc-400">({lead.reviews || 0})</span>
                        </div>
                      ) : "-"}
                    </TableCell>
                    <TableCell>
                      <Badge variant={lead.type === "NO_WEBSITE" ? "destructive" : lead.type === "WEBSITE_REDESIGN" ? "secondary" : "outline"}>
                        {lead.type.replace("_", " ")}
                      </Badge>
                    </TableCell>
                    <TableCell>
                      <Badge variant="outline" className="capitalize">
                        {lead.status || "new"}
                      </Badge>
                    </TableCell>
                    <TableCell>
                      <div className={`font-bold ${lead.score >= 6 ? 'text-emerald-600' : lead.score >= 4 ? 'text-amber-600' : 'text-zinc-500'}`}>
                        {lead.score}/8
                      </div>
                    </TableCell>
                    <TableCell className="text-right">
                      <div className="flex justify-end gap-1">
                        {lead.maps_url && (
                          <Button variant="ghost" size="sm" asChild>
                            <a href={lead.maps_url} target="_blank" rel="noopener noreferrer">
                              <ExternalLink className="h-4 w-4" />
                            </a>
                          </Button>
                        )}
                        <Button variant="ghost" size="sm" onClick={() => openEditDialog(lead)}>
                          <Edit className="h-4 w-4" />
                        </Button>
                        <AlertDialog>
                          <AlertDialogTrigger asChild>
                            <Button variant="ghost" size="sm" className="text-red-600 hover:text-red-700">
                              <Trash2 className="h-4 w-4" />
                            </Button>
                          </AlertDialogTrigger>
                          <AlertDialogContent>
                            <AlertDialogHeader>
                              <AlertDialogTitle>Delete &quot;{lead.name}&quot;?</AlertDialogTitle>
                              <AlertDialogDescription>
                                This action cannot be undone. This lead will be permanently deleted.
                              </AlertDialogDescription>
                            </AlertDialogHeader>
                            <AlertDialogFooter>
                              <AlertDialogCancel>Cancel</AlertDialogCancel>
                              <AlertDialogAction onClick={() => handleDelete(lead.id)} className="bg-red-600 hover:bg-red-700">
                                Delete
                              </AlertDialogAction>
                            </AlertDialogFooter>
                          </AlertDialogContent>
                        </AlertDialog>
                      </div>
                    </TableCell>
                  </TableRow>
                ))
              ) : (
                <TableRow>
                  <TableCell colSpan={8} className="text-center py-8 text-zinc-500 dark:text-zinc-400">
                    No leads found matching your criteria.
                  </TableCell>
                </TableRow>
              )}
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

      {/* Edit Dialog */}
      <Dialog open={!!editingLead} onOpenChange={(open) => !open && setEditingLead(null)}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Edit Lead: {editingLead?.name}</DialogTitle>
            <DialogDescription>
              Update notes, tags, or status for this lead.
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4 py-4">
            <div className="space-y-2">
              <Label htmlFor="status">Status</Label>
              <Select value={editForm.status} onValueChange={(v) => setEditForm(p => ({ ...p, status: v }))}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="new">New</SelectItem>
                  <SelectItem value="contacted">Contacted</SelectItem>
                  <SelectItem value="qualified">Qualified</SelectItem>
                  <SelectItem value="converted">Converted</SelectItem>
                  <SelectItem value="lost">Lost</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div className="space-y-2">
              <Label htmlFor="tags">Tags (comma-separated)</Label>
              <Input
                id="tags"
                value={editForm.tags}
                onChange={(e) => setEditForm(p => ({ ...p, tags: e.target.value }))}
                placeholder="e.g., priority, follow-up, local"
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="notes">Notes</Label>
              <Input
                id="notes"
                value={editForm.notes}
                onChange={(e) => setEditForm(p => ({ ...p, notes: e.target.value }))}
                placeholder="Add notes about this lead..."
              />
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setEditingLead(null)}>Cancel</Button>
            <Button onClick={handleSaveEdit}>Save Changes</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  )
}
