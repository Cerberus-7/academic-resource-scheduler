import { useMemo, useState, lazy, Suspense } from 'react'
import { Routes, Route, Navigate } from 'react-router-dom'
import { ThemeProvider, CssBaseline } from '@mui/material'
import DashboardIcon from '@mui/icons-material/Dashboard'
import CalendarViewWeekIcon from '@mui/icons-material/CalendarViewWeek'
import AutoAwesomeIcon from '@mui/icons-material/AutoAwesome'
import MeetingRoomIcon from '@mui/icons-material/MeetingRoom'
import PeopleIcon from '@mui/icons-material/People'
import MenuBookIcon from '@mui/icons-material/MenuBook'
import PendingActionsIcon from '@mui/icons-material/PendingActions'
import SwapHorizIcon from '@mui/icons-material/SwapHoriz'
import FactCheckIcon from '@mui/icons-material/FactCheck'
import InsightsIcon from '@mui/icons-material/Insights'
import ScienceIcon from '@mui/icons-material/Science'
import SyncIcon from '@mui/icons-material/Sync'
import SearchIcon from '@mui/icons-material/Search'
import AddCircleIcon from '@mui/icons-material/AddCircle'
import ListAltIcon from '@mui/icons-material/ListAlt'
import EventIcon from '@mui/icons-material/Event'
import TrackChangesIcon from '@mui/icons-material/TrackChanges'
import SettingsBackupRestoreIcon from '@mui/icons-material/SettingsBackupRestore'

import { getAppTheme } from './theme/theme'
import { useAuth } from './hooks/useAuth'
import DashboardLayout, { NavItem } from './layouts/DashboardLayout'
import LoginPage from './pages/LoginPage'



import { useQuery } from '@tanstack/react-query'
import { api } from './api/client'
import { CircularProgress, Box as MuiBox } from '@mui/material'

const AdminDashboard = lazy(() => import('./pages/admin/AdminDashboard'))
const TimetableGeneratorPage = lazy(() => import('./pages/admin/TimetableGeneratorPage'))
const ResourcesPage = lazy(() => import('./pages/admin/ResourcesPage'))
const FacultyPage = lazy(() => import('./pages/admin/FacultyPage'))
const CoursesPage = lazy(() => import('./pages/admin/CoursesPage'))
const RequestQueuePage = lazy(() => import('./pages/admin/RequestQueuePage'))
const AuditLogPage = lazy(() => import('./pages/admin/AuditLogPage'))
const AnalyticsPage = lazy(() => import('./pages/admin/AnalyticsPage'))
const OsSimulationPage = lazy(() => import('./pages/admin/OsSimulationPage'))
const SyncDashboardPage = lazy(() => import('./pages/admin/SyncDashboardPage'))
const BackupPage = lazy(() => import('./pages/admin/BackupPage'))
const TimetableViewerPage = lazy(() => import('./pages/TimetableViewerPage'))
const ShiftRequestsPage = lazy(() => import('./pages/ShiftRequestsPage'))
const ShiftDetailPage = lazy(() => import('./pages/ShiftDetailPage'))
const AvailabilitySearchPage = lazy(() => import('./pages/AvailabilitySearchPage'))
const ScheduleRequestFormPage = lazy(() => import('./pages/ScheduleRequestFormPage'))
const MyRequestsPage = lazy(() => import('./pages/MyRequestsPage'))
const ProfessorDashboard = lazy(() => import('./pages/professor/ProfessorDashboard'))

const PROFESSOR_REQUEST_TYPES = [
  { value: 'extra_class', label: 'Extra Class' },
  { value: 'makeup_class', label: 'Makeup Class' },
  { value: 'lab_session', label: 'Lab Session' },
  { value: 'tutorial', label: 'Tutorial' },
  { value: 'remedial_class', label: 'Remedial Class' },
  { value: 'doubt_clearing', label: 'Doubt-Clearing Session' },
  { value: 'project_discussion', label: 'Project Discussion' },
]

const EVENT_REQUEST_TYPES = [
  { value: 'guest_lecture', label: 'Guest Lecture' },
  { value: 'seminar', label: 'Seminar' },
  { value: 'workshop', label: 'Workshop' },
  { value: 'hackathon', label: 'Hackathon' },
  { value: 'coding_competition', label: 'Coding Competition' },
  { value: 'placement_training', label: 'Placement Training' },
  { value: 'examination', label: 'Examination' },
  { value: 'viva_voce', label: 'Viva Voce' },
  { value: 'department_meeting', label: 'Department Meeting' },
  { value: 'orientation', label: 'Orientation' },
  { value: 'project_presentation', label: 'Project Presentation' },
]

function useMyFacultyId() {
  const { user } = useAuth()
  const { data: faculty = [] } = useQuery({ queryKey: ['faculty'], queryFn: () => api.get('/faculty').then(r => r.data), enabled: !!user })
  return faculty.find((f: any) => f.user_id === user?.id)?.id
}

function AdminApp({ mode, toggleMode }: { mode: 'light' | 'dark'; toggleMode: () => void }) {
  const navItems: NavItem[] = [
    { label: 'Dashboard', path: '/admin', icon: <DashboardIcon /> },
    { label: 'Weekly Timetable', path: '/admin/timetable', icon: <CalendarViewWeekIcon /> },
    { label: 'Timetable Generator', path: '/admin/generator', icon: <AutoAwesomeIcon /> },
    { label: 'Rooms & Labs', path: '/admin/resources', icon: <MeetingRoomIcon /> },
    { label: 'Faculty', path: '/admin/faculty', icon: <PeopleIcon /> },
    { label: 'Courses & Sections', path: '/admin/courses', icon: <MenuBookIcon /> },
    { label: 'Request Queue', path: '/admin/queue', icon: <PendingActionsIcon /> },
    { label: 'Shift Approvals', path: '/admin/shifts', icon: <SwapHorizIcon /> },
    { label: 'Audit Log', path: '/admin/audit', icon: <FactCheckIcon /> },
    { label: 'Analytics & Reports', path: '/admin/analytics', icon: <InsightsIcon /> },
    { label: 'OS Simulation', path: '/admin/os-simulation', icon: <ScienceIcon /> },
    { label: 'Sync Dashboard', path: '/admin/sync', icon: <SyncIcon /> },
    { label: 'Backup & Restore', path: '/admin/backup', icon: <SettingsBackupRestoreIcon /> },
  ]
  const fallback = (
    <MuiBox sx={{ display: 'flex', justifyContent: 'center', mt: 8 }}><CircularProgress /></MuiBox>
  )
  return (
    <DashboardLayout navItems={navItems} mode={mode} toggleMode={toggleMode}>
      <Suspense fallback={fallback}>
      <Routes>
        <Route path="/admin" element={<AdminDashboard />} />
        <Route path="/admin/timetable" element={<TimetableViewerPage title="Weekly Timetable" />} />
        <Route path="/admin/generator" element={<TimetableGeneratorPage />} />
        <Route path="/admin/resources" element={<ResourcesPage />} />
        <Route path="/admin/faculty" element={<FacultyPage />} />
        <Route path="/admin/courses" element={<CoursesPage />} />
        <Route path="/admin/queue" element={<RequestQueuePage />} />
        <Route path="/admin/shifts" element={<ShiftRequestsPage title="Shift Approvals" basePath="/admin/shifts" />} />
        <Route path="/admin/shifts/:id" element={<ShiftDetailPage />} />
        <Route path="/admin/audit" element={<AuditLogPage />} />
        <Route path="/admin/analytics" element={<AnalyticsPage />} />
        <Route path="/admin/os-simulation" element={<OsSimulationPage />} />
        <Route path="/admin/sync" element={<SyncDashboardPage />} />
        <Route path="/admin/backup" element={<BackupPage />} />
        <Route path="*" element={<Navigate to="/admin" replace />} />
      </Routes>
      </Suspense>
    </DashboardLayout>
  )
}

function ProfessorApp({ mode, toggleMode }: { mode: 'light' | 'dark'; toggleMode: () => void }) {
  const facultyId = useMyFacultyId()
  const navItems: NavItem[] = [
    { label: 'Dashboard', path: '/professor', icon: <DashboardIcon /> },
    { label: 'My Schedule', path: '/professor/schedule', icon: <CalendarViewWeekIcon /> },
    { label: 'Find Room/Lab', path: '/professor/find-room', icon: <SearchIcon /> },
    { label: 'Request Extra Class', path: '/professor/request', icon: <AddCircleIcon /> },
    { label: 'My Requests', path: '/professor/my-requests', icon: <ListAltIcon /> },
    { label: 'Shift Requests', path: '/professor/shift-requests', icon: <SwapHorizIcon /> },
  ]
  const fallback = (
    <MuiBox sx={{ display: 'flex', justifyContent: 'center', mt: 8 }}><CircularProgress /></MuiBox>
  )
  return (
    <DashboardLayout navItems={navItems} mode={mode} toggleMode={toggleMode}>
      <Suspense fallback={fallback}>
      <Routes>
        <Route path="/professor" element={<ProfessorDashboard />} />
        <Route path="/professor/schedule" element={<TimetableViewerPage title="My Weekly Schedule" defaultFacultyId={facultyId} />} />
        <Route path="/professor/find-room" element={<AvailabilitySearchPage title="Find Room/Lab Availability" />} />
        <Route path="/professor/request" element={<ScheduleRequestFormPage title="Request Extra / Makeup Class" requestTypes={PROFESSOR_REQUEST_TYPES} defaultFacultyId={facultyId} />} />
        <Route path="/professor/my-requests" element={<MyRequestsPage title="My Requests" />} />
        <Route path="/professor/shift-requests" element={<ShiftRequestsPage title="Shift Requests" basePath="/professor/shift-requests" facultyOnly={facultyId} />} />
        <Route path="/professor/shift-requests/:id" element={<ShiftDetailPage />} />
        <Route path="*" element={<Navigate to="/professor" replace />} />
      </Routes>
      </Suspense>
    </DashboardLayout>
  )
}

function CoordinatorApp({ mode, toggleMode }: { mode: 'light' | 'dark'; toggleMode: () => void }) {
  const navItems: NavItem[] = [
    { label: 'Request Event', path: '/coordinator/request', icon: <EventIcon /> },
    { label: 'Resource Search', path: '/coordinator/search', icon: <SearchIcon /> },
    { label: 'Track Requests', path: '/coordinator/tracking', icon: <TrackChangesIcon /> },
  ]
  const fallback = (
    <MuiBox sx={{ display: 'flex', justifyContent: 'center', mt: 8 }}><CircularProgress /></MuiBox>
  )
  return (
    <DashboardLayout navItems={navItems} mode={mode} toggleMode={toggleMode}>
      <Suspense fallback={fallback}>
      <Routes>
        <Route path="/coordinator" element={<Navigate to="/coordinator/request" replace />} />
        <Route path="/coordinator/request" element={<ScheduleRequestFormPage title="Request Room/Lab for Event" requestTypes={EVENT_REQUEST_TYPES} />} />
        <Route path="/coordinator/search" element={<AvailabilitySearchPage title="Resource Search" />} />
        <Route path="/coordinator/tracking" element={<MyRequestsPage title="Event Request Tracking" />} />
        <Route path="*" element={<Navigate to="/coordinator/request" replace />} />
      </Routes>
      </Suspense>
    </DashboardLayout>
  )
}

function StudentApp({ mode, toggleMode }: { mode: 'light' | 'dark'; toggleMode: () => void }) {
  const navItems: NavItem[] = [
    { label: 'Published Timetable', path: '/student/timetable', icon: <CalendarViewWeekIcon /> },
  ]
  const fallback = (
    <MuiBox sx={{ display: 'flex', justifyContent: 'center', mt: 8 }}><CircularProgress /></MuiBox>
  )
  return (
    <DashboardLayout navItems={navItems} mode={mode} toggleMode={toggleMode}>
      <Suspense fallback={fallback}>
      <Routes>
        <Route path="/student" element={<Navigate to="/student/timetable" replace />} />
        <Route path="/student/timetable" element={<TimetableViewerPage title="Published Timetable" readOnlyFilters />} />
        <Route path="*" element={<Navigate to="/student/timetable" replace />} />
      </Routes>
      </Suspense>
    </DashboardLayout>
  )
}

export default function App() {
  const { user } = useAuth()
  const [mode, setMode] = useState<'light' | 'dark'>('light')
  const theme = useMemo(() => getAppTheme(mode), [mode])
  const toggleMode = () => setMode((m) => (m === 'light' ? 'dark' : 'light'))

  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <Routes>
        <Route path="/login" element={user ? <Navigate to="/" replace /> : <LoginPage />} />
        <Route
          path="/*"
          element={
            !user ? <Navigate to="/login" replace /> :
            user.role === 'admin' ? <AdminApp mode={mode} toggleMode={toggleMode} /> :
            user.role === 'professor' ? <ProfessorApp mode={mode} toggleMode={toggleMode} /> :
            user.role === 'event_coordinator' ? <CoordinatorApp mode={mode} toggleMode={toggleMode} /> :
            <StudentApp mode={mode} toggleMode={toggleMode} />
          }
        />
      </Routes>
    </ThemeProvider>
  )
}
