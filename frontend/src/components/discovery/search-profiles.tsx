import { useState } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Select } from '@/components/ui/select'
import { Plus, Play, Trash2, Search, Clock } from 'lucide-react'
import type { SearchProfile, ScheduleFrequency } from '@/services/discovery'

interface SearchProfilesProps {
  profiles: SearchProfile[]
  onCreate: (name: string, keywords: string, location: string | null, schedule: ScheduleFrequency) => void
  onRun: (id: string) => void
  onDelete: (id: string) => void
  isSearching: boolean
}

export function SearchProfiles({ profiles, onCreate, onRun, onDelete, isSearching }: SearchProfilesProps) {
  const [name, setName] = useState('')
  const [keywords, setKeywords] = useState('')
  const [location, setLocation] = useState('')
  const [schedule, setSchedule] = useState<ScheduleFrequency>('manual')
  const [isAdding, setIsAdding] = useState(false)

  const handleCreate = () => {
    if (!name.trim() || !keywords.trim()) return
    onCreate(name.trim(), keywords.trim(), location.trim() || null, schedule)
    setName('')
    setKeywords('')
    setLocation('')
    setSchedule('manual')
    setIsAdding(false)
  }

  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between">
        <CardTitle className="text-lg flex items-center gap-2">
          <Search className="w-5 h-5" />
          Saved Searches
        </CardTitle>
        <Button variant="outline" size="sm" onClick={() => setIsAdding(!isAdding)}>
          <Plus className="w-4 h-4 mr-1" /> New
        </Button>
      </CardHeader>
      <CardContent>
        {isAdding && (
          <div className="mb-4 p-3 border border-glass-border rounded-lg space-y-3">
            <Input placeholder="Profile name..." value={name} onChange={e => setName(e.target.value)} />
            <Input placeholder="Keywords..." value={keywords} onChange={e => setKeywords(e.target.value)} />
            <Input placeholder="Location (optional)..." value={location} onChange={e => setLocation(e.target.value)} />
            <Select value={schedule} onChange={e => setSchedule(e.target.value as ScheduleFrequency)} className="w-full">
              <option value="manual">Manual</option>
              <option value="hourly">Hourly</option>
              <option value="daily">Daily</option>
              <option value="weekly">Weekly</option>
              <option value="monthly">Monthly</option>
            </Select>
            <div className="flex gap-2">
              <Button size="sm" onClick={handleCreate} disabled={!name.trim() || !keywords.trim()}>Create</Button>
              <Button size="sm" variant="ghost" onClick={() => setIsAdding(false)}>Cancel</Button>
            </div>
          </div>
        )}

        {profiles.length === 0 && !isAdding && (
          <p className="text-sm text-muted-foreground">No saved searches yet. Create one to quickly run recurring searches.</p>
        )}

        <div className="space-y-2 max-h-64 overflow-y-auto">
          {profiles.map(profile => (
            <div key={profile.id} className="flex items-center justify-between p-2 rounded-lg hover:bg-dark-800 transition-colors">
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium truncate">{profile.name}</p>
                <p className="text-xs text-muted-foreground truncate">
                  {profile.keywords}
                  {profile.location && ` \u2022 ${profile.location}`}
                </p>
                {profile.scheduleFrequency !== 'manual' && (
                  <p className="text-[10px] text-muted-foreground flex items-center gap-1 mt-0.5">
                    <Clock className="w-3 h-3" /> {profile.scheduleFrequency}
                  </p>
                )}
              </div>
              <div className="flex items-center gap-1 shrink-0">
                <Button variant="ghost" size="icon" className="w-7 h-7" onClick={() => onRun(profile.id)} disabled={isSearching} title="Run search">
                  <Play className="w-3.5 h-3.5" />
                </Button>
                <Button variant="ghost" size="icon" className="w-7 h-7 text-red-400 hover:text-red-300" onClick={() => onDelete(profile.id)} title="Delete">
                  <Trash2 className="w-3.5 h-3.5" />
                </Button>
              </div>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  )
}
