import { useState, useCallback, useEffect, useMemo } from 'react'
import { PageHeader } from '@/components/layout/page-header'
import { Tabs } from '@/components/ui/tabs'
import { MatchCard } from '@/components/matching/match-card'
import { MatchDashboard } from '@/components/matching/match-dashboard'
import { MatchExplanation } from '@/components/matching/match-explanation'
import { SkillGapPanel } from '@/components/matching/skill-gap-panel'
import { MatchHistory } from '@/components/matching/match-history'
import { matchingService } from '@/services/matching/matching'
import { matchHistoryService } from '@/services/matching/history'
import { buildCandidateProfile, createDefaultProfile } from '@/services/matching/candidate-profile'
import { generateSkillGapAnalysis } from '@/services/matching/gap-analysis'
import { discoveryHistoryService } from '@/services/discovery/discovery-history'
import type { MatchResult, CandidateProfile, MatchStatistics, MatchHistoryEntry } from '@/services/matching/types'
import type { Job } from '@/services/discovery/types'
import { Brain, Filter, ArrowUpDown } from 'lucide-react'
import { Select } from '@/components/ui/select'
import { Button } from '@/components/ui/button'

export function MatchingPage() {
  const [results, setResults] = useState<MatchResult[]>([])
  const [selectedMatch, setSelectedMatch] = useState<MatchResult | null>(null)
  const [history, setHistory] = useState<MatchHistoryEntry[]>([])
  const [, setProfile] = useState<CandidateProfile>(createDefaultProfile())
  const [hasProfile, setHasProfile] = useState(false)
  const [activeTab, setActiveTab] = useState('dashboard')
  const [sortField, setSortField] = useState<'match' | 'date' | 'salary'>('match')

  const refreshHistory = useCallback(() => {
    setHistory(matchHistoryService.getRecent(20))
  }, [])

  useEffect(() => { refreshHistory() }, [refreshHistory])

  const handleScoreJobs = useCallback(() => {
    const historyEntries = discoveryHistoryService.getRecent(5)
    const jobs: Job[] = []
    for (const entry of historyEntries) {
      if (entry.uniqueJobs > 0) {
        try {
          const raw = localStorage.getItem(`ajapp_disc_hist_result_${entry.id}`)
          if (raw) {
            const parsed = JSON.parse(raw) as { jobs: Job[] }
            jobs.push(...parsed.jobs)
          }
        } catch {}
      }
    }

    if (jobs.length === 0) return

    const demoProfile = buildCandidateProfile({
      skills: [
        { name: 'TypeScript', category: 'language', proficiency: 5 },
        { name: 'JavaScript', category: 'language', proficiency: 5 },
        { name: 'React', category: 'frontend', proficiency: 4 },
        { name: 'Node.js', category: 'backend', proficiency: 4 },
        { name: 'Python', category: 'language', proficiency: 3 },
        { name: 'Go', category: 'language', proficiency: 2 },
        { name: 'AWS', category: 'cloud', proficiency: 3 },
        { name: 'Docker', category: 'devops', proficiency: 3 },
        { name: 'SQL', category: 'database', proficiency: 4 },
        { name: 'Git', category: 'tools', proficiency: 5 },
        { name: 'GraphQL', category: 'api', proficiency: 3 },
        { name: 'REST', category: 'api', proficiency: 5 },
      ],
      experience: [
        { title: 'Senior Software Engineer', company: 'Tech Corp', startDate: '2021-01-01', isCurrent: true, description: 'Building scalable systems' },
        { title: 'Software Engineer', company: 'Startup Inc', startDate: '2018-03-01', endDate: '2020-12-31', description: 'Full stack development' },
      ],
      education: [
        { institution: 'University of Technology', degree: "Bachelor's", fieldOfStudy: 'Computer Science', gpa: 3.5 },
      ],
      certifications: [
        { name: 'AWS Solutions Architect', issuer: 'Amazon' },
      ],
      location: 'San Francisco, CA',
      remotePreference: 'remote',
      salaryExpectationMin: 120000,
      salaryExpectationMax: 180000,
      salaryCurrency: 'USD',
    })

    setProfile(demoProfile)
    setHasProfile(true)

    const scored = matchingService.scoreBatch(jobs, demoProfile, 'resume_demo_1')
    setResults(scored)
    refreshHistory()
  }, [refreshHistory])

  const sortedResults = useMemo(() => {
    if (sortField === 'date') {
      return [...results].sort((a, b) => new Date(b.job.postedDate || b.job.discoveredAt).getTime() - new Date(a.job.postedDate || a.job.discoveredAt).getTime())
    }
    if (sortField === 'salary') {
      return [...results].sort((a, b) => (b.job.salaryMax || b.job.salaryMin || 0) - (a.job.salaryMax || a.job.salaryMin || 0))
    }
    return results
  }, [results, sortField])

  const statistics: MatchStatistics = useMemo(() => matchingService.getStatistics(results), [results])

  return (
    <div className="space-y-6">
      <PageHeader
        title="AI Matching"
        description="Score discovered jobs against your profile to find the best opportunities."
      />

      <div className="flex items-center gap-3">
        {!hasProfile && (
          <Button onClick={handleScoreJobs} className="flex items-center gap-2">
            <Brain className="w-4 h-4" />
            Score Latest Discovered Jobs
          </Button>
        )}
        {results.length > 0 && (
          <div className="flex items-center gap-2 ml-auto">
            <ArrowUpDown className="w-4 h-4 text-muted-foreground" />
            <Select value={sortField} onChange={e => setSortField(e.target.value as any)} className="w-32 text-sm">
              <option value="match">Best Match</option>
              <option value="date">Newest</option>
              <option value="salary">Highest Salary</option>
            </Select>
          </div>
        )}
      </div>

      {results.length > 0 && (
        <div className="mb-4">
          <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
            <div className="flex gap-1 border-b border-glass-border mb-4">
              {['dashboard', 'matches', 'history'].map(tab => (
                <button
                  key={tab}
                  onClick={() => setActiveTab(tab)}
                  className={`px-4 py-2 text-sm font-medium transition-colors border-b-2 -mb-px ${
                    activeTab === tab ? 'border-primary text-primary' : 'border-transparent text-muted-foreground hover:text-foreground'
                  }`}
                >
                  {tab === 'dashboard' ? 'Dashboard' : tab === 'matches' ? `Matches (${results.length})` : 'History'}
                </button>
              ))}
            </div>
          </Tabs>
        </div>
      )}

      {activeTab === 'dashboard' && results.length > 0 && (
        <MatchDashboard statistics={statistics} totalJobs={results.length} />
      )}

      {activeTab === 'matches' && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="lg:col-span-2 space-y-4">
            {sortedResults.map((match, idx) => (
              <div
                key={match.jobId}
                onClick={() => setSelectedMatch(selectedMatch?.jobId === match.jobId ? null : match)}
                className={`cursor-pointer rounded-lg transition-colors ${
                  selectedMatch?.jobId === match.jobId ? 'ring-2 ring-primary' : ''
                }`}
              >
                <MatchCard match={match} rank={idx + 1} />
              </div>
            ))}
          </div>

          <div className="space-y-4">
            {selectedMatch && (
              <>
                <MatchExplanation match={selectedMatch} />
                <SkillGapPanel analysis={generateSkillGapAnalysis(selectedMatch.skillDetail, selectedMatch.job)} />
              </>
            )}
            {!selectedMatch && (
              <div className="text-center py-12 text-muted-foreground text-sm">
                <Filter className="w-8 h-8 mx-auto mb-2 opacity-50" />
                <p>Click a match to see detailed breakdown and skill gap analysis.</p>
              </div>
            )}
          </div>
        </div>
      )}

      {activeTab === 'history' && <MatchHistory entries={history} />}

      {results.length === 0 && !hasProfile && (
        <div className="text-center py-16 text-muted-foreground">
          <Brain className="w-12 h-12 mx-auto mb-4 opacity-30" />
          <p className="text-lg mb-2">No jobs scored yet</p>
          <p className="text-sm">Run a job discovery search first, then come back here to score the results against your profile.</p>
        </div>
      )}
    </div>
  )
}
