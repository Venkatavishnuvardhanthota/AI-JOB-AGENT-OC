import { useState } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Select } from '@/components/ui/select'
import { interviewService } from '@/services/calendar'
import { useToast } from '@/components/ui/toast'
import { Calendar, Clock, Video, User, FileText, X, Plus } from 'lucide-react'

interface InterviewSchedulerProps {
  defaultDate?: string
  onClose: () => void
  onScheduled: () => void
}

const PLATFORMS = ['Zoom', 'Google Meet', 'Microsoft Teams', 'Phone', 'In Person', 'Other']
const INTERVIEW_TYPES = [
  { value: 'hr_interview', label: 'HR Interview' },
  { value: 'technical_interview', label: 'Technical Interview' },
  { value: 'final_interview', label: 'Final Interview' },
  { value: 'assessment', label: 'Assessment' },
  { value: 'phone_screen', label: 'Phone Screen' },
]

export function InterviewScheduler({ defaultDate, onClose, onScheduled }: InterviewSchedulerProps) {
  const { addToast } = useToast()
  const [form, setForm] = useState({
    applicationId: '',
    title: '',
    subtitle: '',
    date: defaultDate || new Date().toISOString().split('T')[0],
    time: '10:00',
    endTime: '11:00',
    timezone: Intl.DateTimeFormat().resolvedOptions().timeZone,
    type: 'hr_interview' as string,
    platform: 'Zoom',
    meetingUrl: '',
    recruiter: '',
    interviewer: '',
    notes: '',
    preparationNotes: '',
    companyName: '',
  })

  const handleSubmit = () => {
    if (!form.title) {
      addToast('Please enter a job title', 'error')
      return
    }

    interviewService.scheduleInterview({
      applicationId: form.applicationId || `manual_${Date.now()}`,
      title: form.title,
      subtitle: form.subtitle || form.companyName,
      date: form.date,
      time: form.time,
      endDate: form.date,
      endTime: form.endTime,
      timezone: form.timezone,
      type: form.type,
      platform: form.platform,
      meetingUrl: form.meetingUrl,
      recruiter: form.recruiter,
      interviewer: form.interviewer,
      notes: form.notes,
      preparationNotes: form.preparationNotes,
      companyName: form.companyName || form.subtitle,
      applicationStatus: undefined,
      priority: undefined,
    } as any)

    addToast('Interview scheduled', 'success')
    onScheduled()
    onClose()
  }

  return (
    <Card className="max-w-lg mx-auto">
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle className="text-sm flex items-center gap-2">
            <Calendar className="h-4 w-4 text-primary" /> Schedule Interview
          </CardTitle>
          <button onClick={onClose} className="p-1 hover:bg-dark-700 rounded transition-colors">
            <X className="h-4 w-4" />
          </button>
        </div>
      </CardHeader>
      <CardContent className="space-y-3">
        <div className="grid grid-cols-2 gap-3">
          <div className="col-span-2">
            <p className="text-xs text-muted-foreground mb-1">Job Title *</p>
            <Input value={form.title} onChange={(e) => setForm({ ...form, title: e.target.value })} placeholder="e.g. Senior Software Engineer" />
          </div>
          <div>
            <p className="text-xs text-muted-foreground mb-1">Company</p>
            <Input value={form.companyName} onChange={(e) => setForm({ ...form, companyName: e.target.value, subtitle: e.target.value })} placeholder="Company name" />
          </div>
          <div>
            <p className="text-xs text-muted-foreground mb-1">Type</p>
            <Select value={form.type} onChange={(e) => setForm({ ...form, type: e.target.value })}>
              {INTERVIEW_TYPES.map(t => <option key={t.value} value={t.value}>{t.label}</option>)}
            </Select>
          </div>
        </div>

        <div className="grid grid-cols-3 gap-3">
          <div>
            <p className="text-xs text-muted-foreground mb-1 flex items-center gap-1"><Calendar className="h-3 w-3" /> Date</p>
            <Input type="date" value={form.date} onChange={(e) => setForm({ ...form, date: e.target.value })} />
          </div>
          <div>
            <p className="text-xs text-muted-foreground mb-1 flex items-center gap-1"><Clock className="h-3 w-3" /> Start</p>
            <Input type="time" value={form.time} onChange={(e) => setForm({ ...form, time: e.target.value })} />
          </div>
          <div>
            <p className="text-xs text-muted-foreground mb-1">End</p>
            <Input type="time" value={form.endTime} onChange={(e) => setForm({ ...form, endTime: e.target.value })} />
          </div>
        </div>

        <div className="grid grid-cols-2 gap-3">
          <div>
            <p className="text-xs text-muted-foreground mb-1 flex items-center gap-1"><Video className="h-3 w-3" /> Platform</p>
            <Select value={form.platform} onChange={(e) => setForm({ ...form, platform: e.target.value })}>
              {PLATFORMS.map(p => <option key={p} value={p}>{p}</option>)}
            </Select>
          </div>
          <div>
            <p className="text-xs text-muted-foreground mb-1">Meeting URL</p>
            <Input value={form.meetingUrl} onChange={(e) => setForm({ ...form, meetingUrl: e.target.value })} placeholder="https://..." />
          </div>
        </div>

        <div className="grid grid-cols-2 gap-3">
          <div>
            <p className="text-xs text-muted-foreground mb-1 flex items-center gap-1"><User className="h-3 w-3" /> Recruiter</p>
            <Input value={form.recruiter} onChange={(e) => setForm({ ...form, recruiter: e.target.value })} placeholder="Recruiter name" />
          </div>
          <div>
            <p className="text-xs text-muted-foreground mb-1"><User className="h-3 w-3 inline" /> Interviewer</p>
            <Input value={form.interviewer} onChange={(e) => setForm({ ...form, interviewer: e.target.value })} placeholder="Interviewer name" />
          </div>
        </div>

        <div>
          <p className="text-xs text-muted-foreground mb-1 flex items-center gap-1"><FileText className="h-3 w-3" /> Preparation Notes</p>
          <textarea
            value={form.preparationNotes}
            onChange={(e) => setForm({ ...form, preparationNotes: e.target.value })}
            placeholder="Research points, questions to ask, etc."
            className="w-full rounded-md border border-glass-border bg-dark-800 px-3 py-2 text-sm resize-none h-20 focus:outline-none focus:ring-1 focus:ring-primary/50"
          />
        </div>

        <div>
          <p className="text-xs text-muted-foreground mb-1">Notes</p>
          <textarea
            value={form.notes}
            onChange={(e) => setForm({ ...form, notes: e.target.value })}
            placeholder="Additional notes"
            className="w-full rounded-md border border-glass-border bg-dark-800 px-3 py-2 text-sm resize-none h-16 focus:outline-none focus:ring-1 focus:ring-primary/50"
          />
        </div>

        <div className="flex items-center justify-end gap-2 pt-2">
          <Button variant="outline" size="sm" onClick={onClose}>Cancel</Button>
          <Button size="sm" onClick={handleSubmit}>
            <Plus className="h-3 w-3 mr-1" /> Schedule Interview
          </Button>
        </div>
      </CardContent>
    </Card>
  )
}
