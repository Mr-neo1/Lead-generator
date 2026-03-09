import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Save } from "lucide-react"

export default function SettingsPage() {
  return (
    <div className="space-y-6 max-w-4xl mx-auto">
      <div>
        <h2 className="text-3xl font-bold tracking-tight">Settings</h2>
        <p className="text-zinc-500 mt-1">Configure your automated lead engine.</p>
      </div>

      <div className="grid gap-6">
        <Card>
          <CardHeader>
            <CardTitle>Scraping Configuration</CardTitle>
            <CardDescription>
              Adjust the anti-blocking strategy and worker settings.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="delayMin">Min Delay (seconds)</Label>
                <Input id="delayMin" type="number" defaultValue="2" />
              </div>
              <div className="space-y-2">
                <Label htmlFor="delayMax">Max Delay (seconds)</Label>
                <Input id="delayMax" type="number" defaultValue="5" />
              </div>
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="discoveryWorkers">Discovery Workers</Label>
                <Input id="discoveryWorkers" type="number" defaultValue="2" />
              </div>
              <div className="space-y-2">
                <Label htmlFor="fetchWorkers">Detail Fetch Workers</Label>
                <Input id="fetchWorkers" type="number" defaultValue="6" />
              </div>
            </div>
          </CardContent>
          <CardFooter className="border-t p-6">
            <Button>
              <Save className="mr-2 h-4 w-4" />
              Save Changes
            </Button>
          </CardFooter>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Lead Scoring Model</CardTitle>
            <CardDescription>
              Configure how leads are scored based on their attributes.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="scoreNoWebsite">No Website (+ points)</Label>
              <Input id="scoreNoWebsite" type="number" defaultValue="4" />
            </div>
            <div className="space-y-2">
              <Label htmlFor="scoreRating">Rating above 4 (+ points)</Label>
              <Input id="scoreRating" type="number" defaultValue="2" />
            </div>
            <div className="space-y-2">
              <Label htmlFor="scoreReviews">Reviews above 20 (+ points)</Label>
              <Input id="scoreReviews" type="number" defaultValue="1" />
            </div>
            <div className="space-y-2">
              <Label htmlFor="scorePhone">Phone available (+ points)</Label>
              <Input id="scorePhone" type="number" defaultValue="1" />
            </div>
          </CardContent>
          <CardFooter className="border-t p-6">
            <Button>
              <Save className="mr-2 h-4 w-4" />
              Save Changes
            </Button>
          </CardFooter>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Demo Website Generator</CardTitle>
            <CardDescription>
              Configure the template and domain for generated demo sites.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="demoDomain">Demo Domain</Label>
              <Input id="demoDomain" defaultValue="demo.youragency.com" />
            </div>
            <div className="space-y-2">
              <Label htmlFor="templateType">Default Template</Label>
              <Input id="templateType" defaultValue="Modern Business (Tailwind)" />
            </div>
          </CardContent>
          <CardFooter className="border-t p-6">
            <Button>
              <Save className="mr-2 h-4 w-4" />
              Save Changes
            </Button>
          </CardFooter>
        </Card>
      </div>
    </div>
  )
}
