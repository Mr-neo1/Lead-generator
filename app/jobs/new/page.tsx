"use client"

import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { ArrowLeft, MapPin, Search } from "lucide-react"
import Link from "next/link"
import { useRouter } from "next/navigation"
import { useState } from "react"
import { API_URL } from "@/lib/config"

export default function NewJobPage() {
  const router = useRouter()
  const [loading, setLoading] = useState(false)
  const [keyword, setKeyword] = useState("")
  const [location, setLocation] = useState("")
  const [radius, setRadius] = useState("10")
  const [gridSize, setGridSize] = useState("10x10")

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)
    
    try {
      const response = await fetch(`${API_URL}/api/jobs`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          keyword,
          location,
          radius: parseInt(radius),
          grid_size: gridSize
        })
      })
      
      if (response.ok) {
        router.push('/jobs')
      } else {
        alert('Failed to create job')
      }
    } catch (error) {
      console.error(error)
      alert('Error creating job')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="space-y-6 max-w-2xl mx-auto">
      <div className="flex items-center gap-4">
        <Button variant="outline" size="icon" asChild>
          <Link href="/jobs">
            <ArrowLeft className="h-4 w-4" />
          </Link>
        </Button>
        <div>
          <h2 className="text-3xl font-bold tracking-tight">Create Scraping Job</h2>
          <p className="text-zinc-500 mt-1">Configure a new automated lead generation task.</p>
        </div>
      </div>

      <form onSubmit={handleSubmit}>
        <Card>
          <CardHeader>
            <CardTitle>Job Configuration</CardTitle>
            <CardDescription>
              Define the search parameters to find local businesses on Google Maps.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-6">
            <div className="space-y-2">
              <Label htmlFor="keyword">Search Keyword</Label>
              <div className="relative">
                <Search className="absolute left-3 top-2.5 h-4 w-4 text-zinc-500" />
                <Input id="keyword" placeholder="e.g., dentist, gym, salon, clinic" className="pl-9" required value={keyword} onChange={(e) => setKeyword(e.target.value)} />
              </div>
            </div>

            <div className="space-y-2">
              <Label htmlFor="location">Location (City Name)</Label>
              <div className="relative">
                <MapPin className="absolute left-3 top-2.5 h-4 w-4 text-zinc-500" />
                <Input id="location" placeholder="e.g., Ludhiana, Chandigarh" className="pl-9" required value={location} onChange={(e) => setLocation(e.target.value)} />
              </div>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="radius">Search Radius (km)</Label>
                <Input id="radius" type="number" placeholder="10" value={radius} onChange={(e) => setRadius(e.target.value)} min="1" max="100" required />
              </div>

              <div className="space-y-2">
                <Label htmlFor="grid">Grid Density</Label>
                <Select value={gridSize} onValueChange={setGridSize}>
                  <SelectTrigger id="grid">
                    <SelectValue placeholder="Select grid density" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="5x5">5x5 (Low density, faster)</SelectItem>
                    <SelectItem value="10x10">10x10 (Medium density)</SelectItem>
                    <SelectItem value="15x15">15x15 (High density, slower)</SelectItem>
                    <SelectItem value="20x20">20x20 (Very high density)</SelectItem>
                  </SelectContent>
                </Select>
                <p className="text-xs text-zinc-500 mt-1">Higher density yields more results but takes longer.</p>
              </div>
            </div>
          </CardContent>
          <CardFooter className="flex justify-between border-t p-6">
            <Button variant="outline" type="button" asChild>
              <Link href="/jobs">Cancel</Link>
            </Button>
            <Button type="submit" disabled={loading}>
              {loading ? "Creating..." : "Start Scraping Job"}
            </Button>
          </CardFooter>
        </Card>
      </form>
    </div>
  )
}
