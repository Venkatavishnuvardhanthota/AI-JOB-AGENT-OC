import { useState } from 'react'
import { useAuth } from '@/context/AuthContext'
import { useUpdateUser, useChangePassword } from '@/api/hooks'
import { PageHeader } from '@/components/layout/page-header'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { PasswordInput } from '@/components/auth/password-input'
import { Badge } from '@/components/ui/badge'
import { useToast } from '@/components/ui/toast'
import {
  User, Lock, Trash2, Shield, AlertTriangle, Camera, RefreshCw,
} from 'lucide-react'

export function SettingsAccountPage() {
  const { user, resendVerification, deleteAccount } = useAuth()
  const updateUser = useUpdateUser()
  const changePassword = useChangePassword()
  const { addToast } = useToast()

  const [firstName, setFirstName] = useState(user?.first_name || '')
  const [lastName, setLastName] = useState(user?.last_name || '')
  const [currentPassword, setCurrentPassword] = useState('')
  const [newPassword, setNewPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')
  const [resending, setResending] = useState(false)
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false)
  const [deleting, setDeleting] = useState(false)

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

  const handleResendVerification = async () => {
    if (!user?.email) return
    setResending(true)
    try {
      await resendVerification(user.email)
      addToast('Verification email sent!', 'success')
    } catch { addToast('Failed to send verification email', 'error') }
    finally { setResending(false) }
  }

  const handleDeleteAccount = async () => {
    setDeleting(true)
    try {
      await deleteAccount()
      addToast('Account deleted.', 'info')
    } catch { addToast('Failed to delete account', 'error') }
    finally { setDeleting(false) }
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
          <div className="flex items-center gap-4 mb-4">
            <div className="flex h-16 w-16 items-center justify-center rounded-full bg-primary/20 ring-1 ring-primary/30">
              <Camera className="h-6 w-6 text-muted-foreground" />
            </div>
            <div>
              <p className="text-sm font-medium">Profile Picture</p>
              <p className="text-xs text-muted-foreground">Upload a photo (coming soon)</p>
            </div>
          </div>

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
            <div className="flex items-center gap-2">
              <Input value={user?.email || ''} disabled className="flex-1" />
              <Badge variant={user?.is_verified ? 'success' : 'warning'}>
                {user?.is_verified ? 'Verified' : 'Unverified'}
              </Badge>
              {!user?.is_verified && (
                <Button variant="ghost" size="sm" onClick={handleResendVerification} disabled={resending}>
                  <RefreshCw className={`h-3 w-3 mr-1 ${resending ? 'animate-spin' : ''}`} />
                  {resending ? 'Sending...' : 'Resend'}
                </Button>
              )}
            </div>
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
            <PasswordInput
              value={currentPassword}
              onChange={e => setCurrentPassword(e.target.value)}
              placeholder="Enter current password"
              showStrength={false}
            />
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="text-xs text-muted-foreground block mb-1">New Password</label>
              <PasswordInput
                value={newPassword}
                onChange={e => setNewPassword(e.target.value)}
                placeholder="Enter new password"
                showStrength
              />
            </div>
            <div>
              <label className="text-xs text-muted-foreground block mb-1">Confirm New Password</label>
              <PasswordInput
                value={confirmPassword}
                onChange={e => setConfirmPassword(e.target.value)}
                placeholder="Confirm new password"
                showStrength={false}
              />
            </div>
          </div>
          <Button onClick={handleChangePassword} disabled={!currentPassword || !newPassword || changePassword.isPending}>Change Password</Button>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Shield className="h-5 w-5 text-primary" />
            Active Sessions
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex items-center justify-between rounded-lg bg-dark-800 p-3">
            <div className="flex items-center gap-3">
              <div className="h-2 w-2 rounded-full bg-success" />
              <div>
                <p className="text-sm font-medium">Current Session</p>
                <p className="text-xs text-muted-foreground">Active now</p>
              </div>
            </div>
            <Button variant="outline" size="sm" disabled>Log out</Button>
          </div>
          <p className="text-xs text-muted-foreground mt-2">Session management will be available in a future update.</p>
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
          <p className="text-sm text-muted-foreground mb-4">Permanently delete your account and all associated data. This action cannot be undone.</p>
          {!showDeleteConfirm ? (
            <Button variant="destructive" onClick={() => setShowDeleteConfirm(true)}>
              <Trash2 className="h-4 w-4 mr-2" />
              Delete Account
            </Button>
          ) : (
            <div className="rounded-lg border border-error/20 bg-error/5 p-4 space-y-3">
              <div className="flex items-center gap-2 text-sm text-error">
                <AlertTriangle className="h-4 w-4" />
                <span className="font-medium">Are you absolutely sure?</span>
              </div>
              <p className="text-xs text-muted-foreground">This will permanently delete your account, resumes, cover letters, applications, and all associated data.</p>
              <div className="flex gap-2">
                <Button variant="destructive" size="sm" onClick={handleDeleteAccount} disabled={deleting}>
                  {deleting ? 'Deleting...' : 'Yes, delete my account'}
                </Button>
                <Button variant="outline" size="sm" onClick={() => setShowDeleteConfirm(false)}>Cancel</Button>
              </div>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  )
}
