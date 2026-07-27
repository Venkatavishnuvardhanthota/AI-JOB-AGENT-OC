import { useState } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Search, Loader2 } from 'lucide-react'

interface SearchPanelProps {
  onSearch: (keywords: string, location: string) => void
  isSearching: boolean
}

export function SearchPanel({ onSearch, isSearching }: SearchPanelProps) {
  const [keywords, setKeywords] = useState('')
  const [location, setLocation] = useState('')

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (!keywords.trim()) return
    onSearch(keywords.trim(), location.trim())
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-lg flex items-center gap-2">
          <Search className="w-5 h-5" />
          Search Jobs
        </CardTitle>
      </CardHeader>
      <CardContent>
        <form onSubmit={handleSubmit} className="flex flex-col sm:flex-row gap-3">
          <div className="flex-1">
            <Input
              placeholder="Job title, keywords, company..."
              value={keywords}
              onChange={e => setKeywords(e.target.value)}
              disabled={isSearching}
              className="w-full"
            />
          </div>
          <div className="w-full sm:w-48">
            <Input
              placeholder="Location (optional)"
              value={location}
              onChange={e => setLocation(e.target.value)}
              disabled={isSearching}
              className="w-full"
            />
          </div>
          <Button type="submit" disabled={isSearching || !keywords.trim()}>
            {isSearching ? <Loader2 className="w-4 h-4 animate-spin mr-2" /> : <Search className="w-4 h-4 mr-2" />}
            {isSearching ? 'Searching...' : 'Search'}
          </Button>
        </form>
      </CardContent>
    </Card>
  )
}
