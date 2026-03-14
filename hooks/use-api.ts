"use client"

import useSWR, { mutate } from "swr"
import { API_URL } from "@/lib/config"

// Generic fetcher
const fetcher = async (url: string) => {
  const res = await fetch(url)
  if (!res.ok) {
    const error = new Error("An error occurred while fetching the data.")
    throw error
  }
  return res.json()
}

// Stats hook
export function useStats() {
  const { data, error, isLoading, mutate } = useSWR(
    `${API_URL}/api/stats`,
    fetcher,
    { refreshInterval: 30000 } // Refresh every 30 seconds
  )
  
  return {
    stats: data,
    isLoading,
    isError: error,
    refresh: mutate
  }
}

// Advanced stats hook
export function useAdvancedStats() {
  const { data, error, isLoading, mutate } = useSWR(
    `${API_URL}/api/stats/advanced`,
    fetcher,
    { refreshInterval: 60000 }
  )
  
  return {
    advancedStats: data,
    isLoading,
    isError: error,
    refresh: mutate
  }
}

// Leads hook with pagination
interface LeadsParams {
  page?: number
  pageSize?: number
  leadType?: string
  minScore?: number
  category?: string
  status?: string
  search?: string
}

export function useLeads(params: LeadsParams = {}) {
  const { page = 1, pageSize = 50, leadType, minScore, category, status, search } = params
  
  const queryParams = new URLSearchParams()
  queryParams.set("page", page.toString())
  queryParams.set("page_size", pageSize.toString())
  if (leadType && leadType !== "ALL") queryParams.set("lead_type", leadType)
  if (minScore) queryParams.set("min_score", minScore.toString())
  if (category) queryParams.set("category", category)
  if (status && status !== "ALL") queryParams.set("status", status)
  if (search) queryParams.set("search", search)
  
  const { data, error, isLoading, mutate } = useSWR(
    `${API_URL}/api/leads?${queryParams.toString()}`,
    fetcher
  )
  
  return {
    leads: data?.items || [],
    pagination: {
      total: data?.total || 0,
      page: data?.page || 1,
      pageSize: data?.page_size || pageSize,
      totalPages: data?.total_pages || 1,
      hasNext: data?.has_next || false,
      hasPrev: data?.has_prev || false
    },
    isLoading,
    isError: error,
    refresh: mutate
  }
}

// Jobs hook with pagination
interface JobsParams {
  page?: number
  pageSize?: number
  status?: string
  keyword?: string
}

export function useJobs(params: JobsParams = {}) {
  const { page = 1, pageSize = 20, status, keyword } = params
  
  const queryParams = new URLSearchParams()
  queryParams.set("page", page.toString())
  queryParams.set("page_size", pageSize.toString())
  if (status && status !== "ALL") queryParams.set("status", status)
  if (keyword) queryParams.set("keyword", keyword)
  
  const { data, error, isLoading, mutate } = useSWR(
    `${API_URL}/api/jobs?${queryParams.toString()}`,
    fetcher
  )
  
  return {
    jobs: data?.items || [],
    pagination: {
      total: data?.total || 0,
      page: data?.page || 1,
      pageSize: data?.page_size || pageSize,
      totalPages: data?.total_pages || 1
    },
    isLoading,
    isError: error,
    refresh: mutate
  }
}

// Single lead hook
export function useLead(leadId: number | null) {
  const { data, error, isLoading, mutate } = useSWR(
    leadId ? `${API_URL}/api/leads/${leadId}` : null,
    fetcher
  )
  
  return {
    lead: data,
    isLoading,
    isError: error,
    refresh: mutate
  }
}

// Single job hook
export function useJob(jobId: string | null) {
  const { data, error, isLoading, mutate } = useSWR(
    jobId ? `${API_URL}/api/jobs/${jobId}` : null,
    fetcher,
    { refreshInterval: jobId ? 5000 : 0 } // Auto-refresh running jobs
  )
  
  return {
    job: data,
    isLoading,
    isError: error,
    refresh: mutate
  }
}

// API mutation functions
export async function createJob(data: {
  keyword: string
  location: string
  radius: number
  grid_size: string
}) {
  const res = await fetch(`${API_URL}/api/jobs`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data)
  })
  
  if (!res.ok) {
    throw new Error("Failed to create job")
  }
  
  // Invalidate jobs cache
  mutate((key: string) => typeof key === "string" && key.startsWith(`${API_URL}/api/jobs`))
  
  return res.json()
}

export async function deleteJob(jobId: string) {
  const res = await fetch(`${API_URL}/api/jobs/${jobId}`, {
    method: "DELETE"
  })
  
  if (!res.ok) {
    throw new Error("Failed to delete job")
  }
  
  mutate((key: string) => typeof key === "string" && key.startsWith(`${API_URL}/api/jobs`))
  
  return res.json()
}

export async function cancelJob(jobId: string) {
  const res = await fetch(`${API_URL}/api/jobs/${jobId}/cancel`, {
    method: "POST"
  })
  
  if (!res.ok) {
    throw new Error("Failed to cancel job")
  }
  
  mutate((key: string) => typeof key === "string" && key.startsWith(`${API_URL}/api/jobs`))
  
  return res.json()
}

export async function restartJob(jobId: string) {
  const res = await fetch(`${API_URL}/api/jobs/${jobId}/restart`, {
    method: "POST"
  })
  
  if (!res.ok) {
    throw new Error("Failed to restart job")
  }
  
  mutate((key: string) => typeof key === "string" && key.startsWith(`${API_URL}/api/jobs`))
  
  return res.json()
}

export async function updateLead(leadId: number, data: {
  status?: string
  tags?: string
  notes?: string
  is_blacklisted?: boolean
}) {
  const res = await fetch(`${API_URL}/api/leads/${leadId}`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data)
  })
  
  if (!res.ok) {
    throw new Error("Failed to update lead")
  }
  
  mutate((key: string) => typeof key === "string" && key.startsWith(`${API_URL}/api/leads`))
  
  return res.json()
}

export async function deleteLead(leadId: number) {
  const res = await fetch(`${API_URL}/api/leads/${leadId}`, {
    method: "DELETE"
  })
  
  if (!res.ok) {
    throw new Error("Failed to delete lead")
  }
  
  mutate((key: string) => typeof key === "string" && key.startsWith(`${API_URL}/api/leads`))
  
  return res.json()
}

export async function bulkDeleteLeads(leadIds: number[]) {
  const res = await fetch(`${API_URL}/api/leads/bulk-delete`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ lead_ids: leadIds })
  })
  
  if (!res.ok) {
    throw new Error("Failed to delete leads")
  }
  
  mutate((key: string) => typeof key === "string" && key.startsWith(`${API_URL}/api/leads`))
  
  return res.json()
}

export async function bulkUpdateLeads(leadIds: number[], data: {
  status?: string
  tags?: string
  is_blacklisted?: boolean
}) {
  const res = await fetch(`${API_URL}/api/leads/bulk-update`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ lead_ids: leadIds, ...data })
  })
  
  if (!res.ok) {
    throw new Error("Failed to update leads")
  }
  
  mutate((key: string) => typeof key === "string" && key.startsWith(`${API_URL}/api/leads`))
  
  return res.json()
}

export async function seedDemoData() {
  const res = await fetch(`${API_URL}/api/seed`, {
    method: "POST"
  })
  
  if (!res.ok) {
    throw new Error("Failed to seed data")
  }
  
  // Invalidate all caches
  mutate(() => true)
  
  return res.json()
}

// Health check
export async function checkHealth() {
  try {
    const res = await fetch(`${API_URL}/health`)
    if (!res.ok) {
      return null
    }
    return res.json()
  } catch {
    return null
  }
}
