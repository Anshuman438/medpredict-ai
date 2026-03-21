import { useEffect, useState } from 'react'
import MainLayout from '../layouts/MainLayout'
import api from '../services/api'
import jsPDF from 'jspdf'

function History() {
  const [predictions, setPredictions] = useState([])
  const [filtered, setFiltered] = useState([])

  const [search, setSearch] = useState('')
  const [riskFilter, setRiskFilter] = useState('All')
  const [sortOrder, setSortOrder] = useState('newest')
  const [fromDate, setFromDate] = useState('')
  const [toDate, setToDate] = useState('')

  const [dropdownOpen, setDropdownOpen] = useState(null)
  const [selectedItem, setSelectedItem] = useState(null)

  const [currentPage, setCurrentPage] = useState(1)
  const itemsPerPage = 6

  useEffect(() => {
    fetchHistory()
    const interval = setInterval(fetchHistory, 30000)
    return () => clearInterval(interval)
  }, [])

  useEffect(() => {
    applyFilters()
  }, [predictions, search, riskFilter, sortOrder, fromDate, toDate])

  const fetchHistory = async () => {
    try {
      const { data } = await api.get('/predictions/my')
      setPredictions(data)
    } catch (err) {
      console.error('Error fetching history')
    }
  }

  const applyFilters = () => {
    let data = [...predictions]

    if (riskFilter !== 'All') {
      data = data.filter(p => p.risk === riskFilter)
    }

    if (search) {
      data = data.filter(p =>
        p.condition.toLowerCase().includes(search.toLowerCase())
      )
    }

    if (fromDate) {
      data = data.filter(p =>
        new Date(p.createdAt) >= new Date(fromDate)
      )
    }

    if (toDate) {
      data = data.filter(p =>
        new Date(p.createdAt) <= new Date(toDate)
      )
    }

    data.sort((a, b) =>
      sortOrder === 'newest'
        ? new Date(b.createdAt) - new Date(a.createdAt)
        : new Date(a.createdAt) - new Date(b.createdAt)
    )

    setFiltered(data)
    setCurrentPage(1)
  }

  const paginatedData = filtered.slice(
    (currentPage - 1) * itemsPerPage,
    currentPage * itemsPerPage
  )

  const totalPages = Math.ceil(filtered.length / itemsPerPage)

  const exportCSV = () => {
    const rows = filtered.map(p =>
      `${p.condition},${p.risk},${p.confidence},${new Date(p.createdAt).toLocaleDateString()}`
    )

    const csv =
      "Condition,Risk,Confidence,Date\n" + rows.join("\n")

    const blob = new Blob([csv], { type: 'text/csv' })
    const link = document.createElement('a')
    link.href = URL.createObjectURL(blob)
    link.download = 'history.csv'
    link.click()

    setDropdownOpen(null)
  }

  const exportPDF = () => {
    const doc = new jsPDF()
    doc.text('Prediction History', 10, 10)

    filtered.forEach((p, i) => {
      const conf = typeof p.confidence === 'number'
        ? `${(p.confidence * 100).toFixed(1)}%`
        : p.confidence
      doc.text(
        `${i + 1}. ${p.condition} | ${p.risk} | ${conf}`,
        10,
        20 + i * 8
      )
    })

    doc.save('history.pdf')
    setDropdownOpen(null)
  }

  const exportSinglePDF = (item) => {
    const doc = new jsPDF()
    const conf = typeof item.confidence === 'number'
      ? `${(item.confidence * 100).toFixed(1)}%`
      : item.confidence
    doc.setFontSize(16)
    doc.text('MedPredict AI - Diagnostic Report', 10, 15)
    doc.setFontSize(12)
    doc.text(`Condition: ${item.condition}`, 10, 30)
    doc.text(`Risk Level: ${item.risk}`, 10, 40)
    doc.text(`Confidence: ${conf}`, 10, 50)
    doc.text(`Date: ${new Date(item.createdAt).toLocaleDateString()}`, 10, 60)

    let y = 75
    const sections = [
      { title: 'Exercise', items: item.recommendations?.exercise || [] },
      { title: 'Diet', items: item.recommendations?.diet || [] },
      { title: 'Lifestyle', items: item.recommendations?.lifestyle || [] },
    ]
    sections.forEach(sec => {
      if (sec.items.length > 0) {
        doc.setFontSize(13)
        doc.text(sec.title, 10, y)
        y += 8
        doc.setFontSize(11)
        sec.items.forEach(rec => {
          doc.text(`  - ${rec}`, 12, y)
          y += 7
        })
        y += 4
      }
    })

    doc.save(`report_${item.condition.replace(/\s+/g, '_')}.pdf`)
  }

  return (
    <MainLayout>

      <div className="history-wrapper">

        <div className="history-header">

          <h2>Prediction History</h2>

          <div className="header-actions">

            {/* FILTER DROPDOWN */}
            <div className="export-dropdown">
              <button
                className="filter-toggle-btn"
                onClick={() =>
                  setDropdownOpen(dropdownOpen === 'filter' ? null : 'filter')
                }
              >
                Filters ⚙
              </button>

              {dropdownOpen === 'filter' && (
                <div className="dropdown-panel">

                  <div className="dropdown-group">
                    <label>Search</label>
                    <input
                      type="text"
                      placeholder="Condition..."
                      value={search}
                      onChange={e => setSearch(e.target.value)}
                    />
                  </div>

                  <div className="dropdown-group">
                    <label>Risk</label>
                    <select
                      value={riskFilter}
                      onChange={e => setRiskFilter(e.target.value)}
                    >
                      <option value="All">All</option>
                      <option value="Low">Low</option>
                      <option value="Medium">Medium</option>
                      <option value="High">High</option>
                    </select>
                  </div>

                  <div className="dropdown-group">
                    <label>Sort</label>
                    <select
                      value={sortOrder}
                      onChange={e => setSortOrder(e.target.value)}
                    >
                      <option value="newest">Newest</option>
                      <option value="oldest">Oldest</option>
                    </select>
                  </div>

                  <div className="dropdown-group">
                    <label>From</label>
                    <input
                      type="date"
                      value={fromDate}
                      onChange={e => setFromDate(e.target.value)}
                    />
                  </div>

                  <div className="dropdown-group">
                    <label>To</label>
                    <input
                      type="date"
                      value={toDate}
                      onChange={e => setToDate(e.target.value)}
                    />
                  </div>

                </div>
              )}
            </div>

            {/* EXPORT DROPDOWN */}
            <div className="export-dropdown">
              <button
                className="export-btn"
                onClick={() =>
                  setDropdownOpen(dropdownOpen === 'export' ? null : 'export')
                }
              >
                Export ⬇
              </button>

              {dropdownOpen === 'export' && (
                <div className="dropdown-panel export-group">
                  <button className="export-btn csv" onClick={exportCSV}>
                    <svg width="18" height="18" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/></svg>
                    Export CSV
                  </button>
                  <button className="export-btn pdf" onClick={exportPDF}>
                    <svg width="18" height="18" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path d="M7 21h10a2 2 0 002-2V9.414a1 1 0 00-.293-.707l-5.414-5.414A1 1 0 0012.586 3H7a2 2 0 00-2 2v14a2 2 0 002 2z" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/></svg>
                    Export PDF
                  </button>
                </div>
              )}
            </div>

          </div>

        </div>

        <div className="glass-table">
          <table>
            <thead>
              <tr>
                <th>Date</th>
                <th>Condition</th>
                <th>Risk</th>
                <th>Confidence</th>
                <th>Details</th>
              </tr>
            </thead>
            <tbody>
              {paginatedData.map(item => (
                <tr key={item._id}>
                  <td>{new Date(item.createdAt).toLocaleDateString()}</td>
                  <td>{item.condition}</td>
                  <td>
                    <span className={`risk-badge ${item.risk.toLowerCase()}`}>
                      {item.risk}
                    </span>
                  </td>
                  <td>{typeof item.confidence === 'number' ? `${(item.confidence * 100).toFixed(1)}%` : item.confidence}</td>
                  <td>
                    <button
                      className="view-btn"
                      onClick={() => setSelectedItem(item)}
                    >
                      👁 View
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {/* Pagination */}
        {totalPages > 1 && (
          <div className="pagination">
            {Array.from({ length: totalPages }, (_, i) => (
              <button
                key={i}
                className={currentPage === i + 1 ? 'active' : ''}
                onClick={() => setCurrentPage(i + 1)}
              >
                {i + 1}
              </button>
            ))}
          </div>
        )}

        {/* Modal */}
        {selectedItem && (
          <div className="modal-overlay" onClick={() => setSelectedItem(null)}>
            <div className="analysis-modal medical-theme" onClick={e => e.stopPropagation()}>
              <button className="modal-close" onClick={() => setSelectedItem(null)}>×</button>
              
              <div className="modal-header-ai">
                <div className="report-badge">Diagnostic Report</div>
                <h2>{selectedItem.condition}</h2>
                <p className="report-date">Generated on {new Date(selectedItem.createdAt).toLocaleDateString()}</p>
              </div>

              <div className="risk-score-display">
                <div className={`risk-indicator ${selectedItem.risk.toLowerCase()}`}>
                  <span className="risk-label">Risk Level</span>
                  <span className="risk-value">{selectedItem.risk}</span>
                </div>
              </div>

              <div className="modal-body-content">
                <div className="section-title">Analysis Summary</div>
                <p className="summary-text">{selectedItem.summary || "No summary available for this report."}</p>
                
                <div className="section-title">Key Recommendations</div>
                {['exercise', 'diet', 'lifestyle'].map(section => (
                  selectedItem.recommendations?.[section]?.length > 0 && (
                    <div key={section}>
                      <h5 style={{ textTransform: 'capitalize', margin: '8px 0 4px' }}>{section}</h5>
                      <ul className="recommendations-list">
                        {selectedItem.recommendations[section].map((rec, i) => (
                          <li key={i} className="rec-item">
                            <span className="check-icon">✓</span> {rec}
                          </li>
                        ))}
                      </ul>
                    </div>
                  )
                ))}
              </div>

              <div className="modal-footer">
                <button className="export-btn pdf" onClick={() => exportSinglePDF(selectedItem)}>
                  Download PDF
                </button>
              </div>
            </div>
          </div>
        )}

      </div>

    </MainLayout>
  )
}

export default History