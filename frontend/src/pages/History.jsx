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
      doc.text(
        `${i + 1}. ${p.condition} | ${p.risk} | ${p.confidence}`,
        10,
        20 + i * 8
      )
    })

    doc.save('history.pdf')
    setDropdownOpen(null)
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
                <div className="dropdown-panel">
                  <div onClick={exportCSV}>Export as CSV</div>
                  <div onClick={exportPDF}>Export as PDF</div>
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
                  <td>{item.confidence}</td>
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
          <div
            className="modal-overlay"
            onClick={() => setSelectedItem(null)}
          >
            <div
              className="modal"
              onClick={e => e.stopPropagation()}
            >
              <h3>Detailed Analysis</h3>
              <p><strong>Condition:</strong> {selectedItem.condition}</p>
              <p><strong>Risk:</strong> {selectedItem.risk}</p>
              <p><strong>Confidence:</strong> {selectedItem.confidence}</p>
              <p><strong>Symptoms:</strong> {selectedItem.symptoms.join(', ')}</p>

              <button
                className="export-btn"
                style={{ marginTop: '1rem' }}
                onClick={() => setSelectedItem(null)}
              >
                Close
              </button>
            </div>
          </div>
        )}

      </div>

    </MainLayout>
  )
}

export default History