import { PageHeader } from '@/components/layout/page-header'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Select } from '@/components/ui/select'
import { useToast } from '@/components/ui/toast'
import { Bell, Globe, Palette } from 'lucide-react'

export function SettingsPreferencesPage() {
  const { addToast } = useToast()

  const handleSave = () => {
    addToast('Preferences saved!', 'success')
  }

  return (
    <div className="space-y-6 max-w-2xl">
      <PageHeader title="Preferences" description="Customize your experience." />

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Bell className="h-5 w-5 text-primary" />
            Notifications
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          {['New job matches', 'Application status updates', 'Pipeline completions', 'System alerts'].map(item => (
            <label key={item} className="flex items-center justify-between">
              <span className="text-sm">{item}</span>
              <input type="checkbox" defaultChecked className="accent-primary" />
            </label>
          ))}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Globe className="h-5 w-5 text-primary" />
            Job Preferences
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div>
            <label className="text-xs text-muted-foreground block mb-1">Preferred Job Types</label>
            <Select defaultValue="">
              <option value="">All Types</option>
              <option value="full-time">Full-time</option>
              <option value="part-time">Part-time</option>
              <option value="contract">Contract</option>
              <option value="internship">Internship</option>
            </Select>
          </div>
          <div>
            <label className="text-xs text-muted-foreground block mb-1">Remote Preference</label>
            <Select defaultValue="any">
              <option value="any">Any</option>
              <option value="remote">Remote Only</option>
              <option value="onsite">On-site Only</option>
              <option value="hybrid">Hybrid</option>
            </Select>
          </div>
          <div>
            <label className="text-xs text-muted-foreground block mb-1">Minimum Salary (USD)</label>
            <Input type="number" placeholder="e.g. 80000" />
          </div>
          <Button onClick={handleSave}>Save Preferences</Button>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Palette className="h-5 w-5 text-primary" />
            Appearance
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm">Dark Mode</p>
              <p className="text-xs text-muted-foreground">Currently using dark theme</p>
            </div>
            <input type="checkbox" defaultChecked disabled className="accent-primary" />
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
