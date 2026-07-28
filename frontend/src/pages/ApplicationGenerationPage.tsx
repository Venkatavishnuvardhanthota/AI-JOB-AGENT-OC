import { useState } from 'react'
import { PageHeader } from '@/components/layout/page-header'
import { GenerationDashboard } from '@/components/application-generation/generation-dashboard'
import { GenerationWizard } from '@/components/application-generation/generation-wizard'
import { PackageList } from '@/components/application-generation/package-list'
import { Wand2, Package } from 'lucide-react'

export function ApplicationGenerationPage() {
  const [activeTab, setActiveTab] = useState<'dashboard' | 'generate' | 'packages'>('dashboard')

  return (
    <div className="space-y-6">
      <PageHeader
        title="Application Generation"
        description="Generate tailored application packages including resumes, cover letters, and questionnaire answers."
      />

      <div className="flex gap-1 border-b border-glass-border">
        {[
          { key: 'dashboard', label: 'Dashboard', icon: Package },
          { key: 'generate', label: 'Generate', icon: Wand2 },
          { key: 'packages', label: 'Packages', icon: Package },
        ].map(tab => (
          <button
            key={tab.key}
            onClick={() => setActiveTab(tab.key as typeof activeTab)}
            className={`flex items-center gap-2 px-4 py-2 text-sm font-medium transition-colors border-b-2 -mb-px ${
              activeTab === tab.key ? 'border-primary text-primary' : 'border-transparent text-muted-foreground hover:text-foreground'
            }`}
          >
            <tab.icon className="h-4 w-4" />
            {tab.label}
          </button>
        ))}
      </div>

      {activeTab === 'dashboard' && <GenerationDashboard />}
      {activeTab === 'generate' && (
        <div className="max-w-2xl">
          <GenerationWizard />
        </div>
      )}
      {activeTab === 'packages' && <PackageList />}
    </div>
  )
}
