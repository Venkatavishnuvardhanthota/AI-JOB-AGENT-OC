import { useState } from 'react'
import { useAuth } from '@/context/AuthContext'
import { useUpdateUser, useChangePassword } from '@/api/hooks'
import { PageHeader } from '@/components/layout/page-header'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { useToast } from '@/components/ui/toast'
import { User, Lock, Trash2 } from 'lucide-react'

export function SettingsAccountPage() {
  const { user } = useAuth()
  const updateUser = useUpdateUser()
  const changePassword = useChangePassword()
  const { addToast } = useToast()

  const [firstName, setFirstName] = useState(user?.first_name || '')
  const [lastName, setLastName] = useState(user?.last_name || '')
  const [currentPassword, setCurrentPassword] = useState('')
  const [newPassword, setNewPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')

  const handleUpdateProfile = async () => {
    try {
      await updateUser.mutateAsync({ first_name: firstName, last_name: lastName })
      addToast('Profile updated!', 'success')
    } catch { addToast('Failed to update profile', 'error') }
  }

  const handleChangePassword = async () => {
    if (newPassword !== confirmPassword) {
      addToast('Passwords do not match', 'error')
      return
    }
    try {
      await changePassword.mutateAsync({ current_password: currentPassword, new_password: newPassword })
      addToast('Password changed!', 'success')
      setCurrentPassword('')
      setNewPassword('')
      setConfirmPassword('')
    } catch { addToast('Failed to change password', 'error') }
  }

  return (
    <div className="space-y-6 max-w-2xl">
      <PageHeader title="Account Settings" description="Manage your account details and security." />

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <User className="h-5 w-5 text-primary" />
            Profile Information
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="text-xs text-muted-foreground block mb-1">First Name</label>
              <Input value={firstName} onChange={e => setFirstName(e.target.value)} />
            </div>
            <div>
              <label className="text-xs text-muted-foreground block mb-1">Last Name</label>
              <Input value={lastName} onChange={e => setLastName(e.target.value)} />
            </div>
          </div>
          <div>
            <label className="text-xs text-muted-foreground block mb-1">Email</label>
            <Input value={user?.email || ''} disabled />
            <p className="text-xs text-muted-foreground mt-1">Email cannot be changed.</p>
          </div>
          <Button onClick={handleUpdateProfile} disabled={updateUser.isPending}>Save Changes</Button>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Lock className="h-5 w-5 text-primary" />
            Change Password
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div>
            <label className="text-xs text-muted-foreground block mb-1">Current Password</label>
            <Input type="password" value={currentPassword} onChange={e => setCurrentPassword(e.target.value)} />
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="text-xs text-muted-foreground block mb-1">New Password</label>
              <Input type="password" value={newPassword} onChange={e => setNewPassword(e.target.value)} />
            </div>
            <div>
              <label className="text-xs text-muted-foreground block mb-1">Confirm New Password</label>
              <Input type="password" value={confirmPassword} onChange={e => setConfirmPassword(e.target.value)} />
            </div>
          </div>
          <Button onClick={handleChangePassword} disabled={!currentPassword || !newPassword || changePassword.isPending}>Change Password</Button>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-error">
            <Trash2 className="h-5 w-5" />
            Danger Zone
          </CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-muted-foreground mb-4">Permanently delete your account and all associated data.</p>
          <Button variant="destructive">Delete Account</Button>
        </CardContent>
      </Card>
    </div>
  )
}
