"use client"

import { Button } from "@/components/ui/button"
import { ChevronLeft, ChevronRight, ChevronsLeft, ChevronsRight } from "lucide-react"

interface PaginationProps {
  page: number
  totalPages: number
  onPageChange: (page: number) => void
  hasNext?: boolean
  hasPrev?: boolean
}

export function Pagination({ page, totalPages, onPageChange, hasNext = true, hasPrev = true }: PaginationProps) {
  const canGoPrev = page > 1 && hasPrev
  const canGoNext = page < totalPages && hasNext
  
  // Calculate page range to show
  const getPageRange = () => {
    const range: number[] = []
    const maxVisible = 5
    
    let start = Math.max(1, page - Math.floor(maxVisible / 2))
    const end = Math.min(totalPages, start + maxVisible - 1)
    
    // Adjust start if we're near the end
    if (end - start < maxVisible - 1) {
      start = Math.max(1, end - maxVisible + 1)
    }
    
    for (let i = start; i <= end; i++) {
      range.push(i)
    }
    
    return range
  }
  
  if (totalPages <= 1) return null
  
  return (
    <div className="flex items-center justify-center gap-1">
      <Button
        variant="outline"
        size="icon"
        className="h-8 w-8"
        onClick={() => onPageChange(1)}
        disabled={!canGoPrev}
      >
        <ChevronsLeft className="h-4 w-4" />
      </Button>
      <Button
        variant="outline"
        size="icon"
        className="h-8 w-8"
        onClick={() => onPageChange(page - 1)}
        disabled={!canGoPrev}
      >
        <ChevronLeft className="h-4 w-4" />
      </Button>
      
      {getPageRange().map((p) => (
        <Button
          key={p}
          variant={p === page ? "default" : "outline"}
          size="icon"
          className="h-8 w-8"
          onClick={() => onPageChange(p)}
        >
          {p}
        </Button>
      ))}
      
      <Button
        variant="outline"
        size="icon"
        className="h-8 w-8"
        onClick={() => onPageChange(page + 1)}
        disabled={!canGoNext}
      >
        <ChevronRight className="h-4 w-4" />
      </Button>
      <Button
        variant="outline"
        size="icon"
        className="h-8 w-8"
        onClick={() => onPageChange(totalPages)}
        disabled={!canGoNext}
      >
        <ChevronsRight className="h-4 w-4" />
      </Button>
    </div>
  )
}
