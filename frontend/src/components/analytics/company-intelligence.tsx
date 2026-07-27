import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import type { CompanyIntelligence as CI } from '@/services/analytics'
import { Building2, MapPin, TrendingUp, TrendingDown, Minus } from 'lucide-react'

interface CompanyIntelligenceProps {
  data: CI[]
  loading: boolean
}

export function CompanyIntelligence({ data, loading }: CompanyIntelligenceProps) {
  if (loading) {
    return <Card><CardContent className="p-6"><div className="h-48 bg-dark-700 rounded animate-pulse" /></CardContent></Card>
  }

  if (data.length === 0) {
    return (
      <Card>
        <CardHeader><CardTitle>Company Intelligence</CardTitle></CardHeader>
        <CardContent>
          <p className="text-sm text-muted-foreground text-center py-6">No company data available yet.</p>
        </CardContent>
      </Card>
    )
  }

  const topByRate = data.sort((a, b) => b.interviewRate - a.interviewRate).slice(0, 10)

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          Company Intelligence
          <Badge variant="outline" className="text-xs">{data.length} companies</Badge>
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-2">
          {topByRate.map((company, i) => (
            <div key={company.company} className="flex items-center gap-3 p-2 rounded-lg hover:bg-dark-800 transition-colors">
              <span className="text-xs text-muted-foreground w-5 shrink-0">{i + 1}.</span>
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2">
                  <Building2 className="h-3.5 w-3.5 text-muted-foreground shrink-0" />
                  <span className="text-sm font-medium truncate">{company.company}</span>
                  {company.locations.length > 0 && (
                    <span className="text-xs text-muted-foreground truncate flex items-center gap-0.5">
                      <MapPin className="h-2.5 w-2.5" />{company.locations.join(', ')}
                    </span>
                  )}
                </div>
                <div className="flex flex-wrap items-center gap-x-3 gap-y-0.5 mt-0.5">
                  <span className="text-xs text-muted-foreground">{company.applications} apps</span>
                  <span className="text-xs text-muted-foreground">•</span>
                  <span className="text-xs text-muted-foreground">{company.interviews} int</span>
                  <span className="text-xs text-muted-foreground">•</span>
                  <span className="text-xs text-green-400">{company.offers} off</span>
                  {company.recruiters.length > 0 && (
                    <>
                      <span className="text-xs text-muted-foreground">•</span>
                      <span className="text-xs text-muted-foreground">{company.recruiters.join(', ')}</span>
                    </>
                  )}
                </div>
              </div>
              <div className="text-right shrink-0">
                <div className="flex items-center gap-1 justify-end">
                  {company.interviewRate > 40 ? <TrendingUp className="h-3 w-3 text-green-400" /> : company.interviewRate > 15 ? <Minus className="h-3 w-3 text-muted-foreground" /> : <TrendingDown className="h-3 w-3 text-warning" />}
                  <span className="text-sm font-medium">{company.interviewRate}%</span>
                </div>
                <p className="text-[10px] text-muted-foreground">interview rate</p>
              </div>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  )
}
