import { useMemo } from 'react'
import { useJobs } from '@/api/hooks'
import { Card, CardContent } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Skeleton } from '@/components/ui/skeleton'
import { Building2, Globe, MapPin, Target, Heart, Cpu } from 'lucide-react'

interface CompanyIntelProps {
  jobId?: string
  companyName?: string
}

export function CompanyIntel({ jobId, companyName }: CompanyIntelProps) {
  const { data: jobs, isLoading } = useJobs() as any
  const jobList = (jobs as any) || []

  const job = useMemo(() => {
    if (jobId) return jobList.find((j: any) => j.id === jobId)
    if (companyName) return jobList.find((j: any) => j.company?.toLowerCase() === companyName.toLowerCase())
    return null
  }, [jobId, companyName, jobList])

  const company = job?.company_details as any
  const hasData = job && (company || job.company)

  if (isLoading) {
    return (
      <Card>
        <CardContent className="p-4 space-y-2">
          <Skeleton className="h-4 w-32" />
          <Skeleton className="h-3 w-48" />
          <Skeleton className="h-3 w-40" />
        </CardContent>
      </Card>
    )
  }

  if (!hasData) {
    return (
      <Card className="border-glass-border">
        <CardContent className="p-4 text-center">
          <Building2 className="h-8 w-8 mx-auto mb-2 text-muted-foreground/50" />
          <p className="text-sm text-muted-foreground">No company information available</p>
          <p className="text-xs text-muted-foreground/60 mt-1">
            {companyName ? `Company data for "${companyName}" not found` : 'Link a job to see company details'}
          </p>
        </CardContent>
      </Card>
    )
  }

  return (
    <Card className="border-glass-border">
      <CardContent className="p-4 space-y-3">
        <div className="flex items-center gap-2">
          <Building2 className="h-4 w-4 text-accent" />
          <h3 className="text-sm font-semibold">{company?.name || job.company}</h3>
        </div>

        {company?.industry && (
          <div className="flex items-center gap-2 text-xs text-muted-foreground">
            <Target className="h-3 w-3" />
            <span>{company.industry}</span>
          </div>
        )}

        {company?.headquarters && (
          <div className="flex items-center gap-2 text-xs text-muted-foreground">
            <MapPin className="h-3 w-3" />
            <span>{company.headquarters}</span>
          </div>
        )}

        {company?.website && (
          <div className="flex items-center gap-2 text-xs">
            <Globe className="h-3 w-3 text-muted-foreground" />
            <a href={company.website} target="_blank" rel="noopener noreferrer" className="text-accent hover:underline">
              {new URL(company.website).hostname}
            </a>
          </div>
        )}

        {company?.mission && (
          <div>
            <p className="text-xs text-muted-foreground mb-1">Mission</p>
            <p className="text-xs leading-relaxed">{company.mission}</p>
          </div>
        )}

        {company?.values && company.values.length > 0 && (
          <div>
            <p className="text-xs text-muted-foreground mb-1 flex items-center gap-1">
              <Heart className="h-3 w-3" /> Values
            </p>
            <div className="flex flex-wrap gap-1">
              {company.values.map((v: string) => (
                <Badge key={v} variant="secondary" className="text-[10px]">{v}</Badge>
              ))}
            </div>
          </div>
        )}

        {company?.technologies && company.technologies.length > 0 && (
          <div>
            <p className="text-xs text-muted-foreground mb-1 flex items-center gap-1">
              <Cpu className="h-3 w-3" /> Technologies
            </p>
            <div className="flex flex-wrap gap-1">
              {company.technologies.map((t: string) => (
                <Badge key={t} variant="outline" className="text-[10px]">{t}</Badge>
              ))}
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  )
}
