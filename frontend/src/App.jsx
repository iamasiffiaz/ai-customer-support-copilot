import { Navigate, Route, Routes, useLocation } from 'react-router-dom'
import Sidebar from './components/Sidebar.jsx'
import Topbar from './components/Topbar.jsx'
import Landing from './pages/Landing.jsx'
import Dashboard from './pages/Dashboard.jsx'
import Tickets from './pages/Tickets.jsx'
import TicketDetails from './pages/TicketDetails.jsx'
import KnowledgeBase from './pages/KnowledgeBase.jsx'
import CopilotChat from './pages/CopilotChat.jsx'
import Replies from './pages/Replies.jsx'
import Escalations from './pages/Escalations.jsx'
import Analytics from './pages/Analytics.jsx'
import Recommendations from './pages/Recommendations.jsx'
import Settings from './pages/Settings.jsx'

function AppLayout({ children }) {
  return (
    <div className="app-shell bg-[var(--color-surface)]">
      <Sidebar />
      <div className="min-w-0 flex flex-col">
        <Topbar />
        <main className="page flex-1">
          <div className="page-inner">{children}</div>
        </main>
      </div>
    </div>
  )
}

export default function App() {
  const location = useLocation()
  const isLanding = location.pathname === '/'

  if (isLanding) {
    return (
      <Routes>
        <Route path="/" element={<Landing />} />
      </Routes>
    )
  }

  return (
    <AppLayout>
      <Routes>
        <Route path="/dashboard" element={<Dashboard />} />
        <Route path="/tickets" element={<Tickets />} />
        <Route path="/tickets/:id" element={<TicketDetails />} />
        <Route path="/knowledge-base" element={<KnowledgeBase />} />
        <Route path="/copilot" element={<CopilotChat />} />
        <Route path="/replies" element={<Replies />} />
        <Route path="/escalations" element={<Escalations />} />
        <Route path="/analytics" element={<Analytics />} />
        <Route path="/recommendations" element={<Recommendations />} />
        <Route path="/settings" element={<Settings />} />
        <Route path="*" element={<Navigate to="/dashboard" replace />} />
      </Routes>
    </AppLayout>
  )
}
