import { useState } from 'react'
import Layout from './components/Layout'
import Dashboard from './pages/Dashboard'
import Companies from './pages/Companies'
import RunPipeline from './pages/RunPipeline'
import Models from './pages/Models'

type PageType = 'dashboard' | 'companies' | 'run-pipeline' | 'models'

function App() {
  const [currentPage, setCurrentPage] = useState<PageType>('dashboard')
  const [selectedCompanyId, setSelectedCompanyId] = useState<string | null>(null)

  const renderPage = () => {
    switch (currentPage) {
      case 'dashboard':
        return <Dashboard />
      case 'companies':
        return <Companies onSelectCompany={(id) => setSelectedCompanyId(id)} />
      case 'run-pipeline':
        return <RunPipeline />
      case 'models':
        return <Models />
      default:
        return <Dashboard />
    }
  }

  return (
    <Layout currentPage={currentPage} onNavigate={setCurrentPage}>
      {renderPage()}
    </Layout>
  )
}

export default App
