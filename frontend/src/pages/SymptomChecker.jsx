import { useState, useEffect } from 'react'
import MainLayout from '../layouts/MainLayout'
import api from '../services/api'
import AnalyzingLoader from '../components/AnalyzingLoader'
import jsPDF from 'jspdf'
import html2canvas from 'html2canvas'

const symptomOptions = [
  'Fever','Headache','Fatigue','Cough','Chest Pain',
  'Shortness of Breath','Nausea','Dizziness','Sore Throat',
  'Body Ache','Blurred Vision','Rapid Heartbeat',
  'Chills','Loss of Appetite','Insomnia',
  'Acidity', 'Indigestion', 'Stomach Pain', 'Vomiting', 
  'Skin Rash', 'Itching', 'Joint Pain', 'Sweating', 'Weight Loss'
]

function SymptomChecker() {
  const [selected, setSelected] = useState([])
  const [search, setSearch] = useState('')
  const [result, setResult] = useState(null)
  const [loading, setLoading] = useState(false)
  const [noteText, setNoteText] = useState('')
  const [savingNote, setSavingNote] = useState(false)
  const [showModal, setShowModal] = useState(false)
  const [error, setError] = useState(null)
  const [showFullRec, setShowFullRec] = useState(false)

  useEffect(() => {
    const stored = localStorage.getItem('analysisResult')
    if (stored) {
      setResult(JSON.parse(stored))
      setShowModal(true)
    }
  }, [])

  useEffect(() => {
    if (result) {
      localStorage.setItem('analysisResult', JSON.stringify(result))
    }
  }, [result])

  const toggleSymptom = (symptom) => {
    setSelected(prev =>
      prev.includes(symptom)
        ? prev.filter(item => item !== symptom)
        : [...prev, symptom]
    )
  }

  const handleSubmit = async () => {
    if (selected.length === 0) {
      setError('Please select at least one symptom')
      return
    }

    try {
      setLoading(true)
      setError(null)

      const { data } = await api.post('/predictions/analyze', {
        symptoms: selected
      })

      setResult(data)
      setShowModal(true)
      setSelected([])

    } catch (err) {
      console.error(err.message)
      setError('Prediction failed.')
    } finally {
      setLoading(false)
    }
  }

  const handleSaveNote = async () => {
    if (!noteText.trim()) return alert('Please write note details')

    try {
      setSavingNote(true)

      await api.post('/notes', {
        title: result?.condition || 'Symptom Analysis',
        comment: `Risk Level: ${result?.risk}`,
        text: noteText
      })

      alert('Note saved successfully')
      setNoteText('')
    } catch (error) {
      alert('Failed to save note')
    } finally {
      setSavingNote(false)
    }
  }

  const exportPDF = async () => {
    const element = document.querySelector('.analysis-modal')
    const canvas = await html2canvas(element)
    const imgData = canvas.toDataURL('image/png')
    const pdf = new jsPDF()
    pdf.addImage(imgData, 'PNG', 10, 10, 190, 0)
    pdf.save('Health_Report.pdf')
  }

  const removeReport = () => {
    setResult(null)
    setShowModal(false)
    localStorage.removeItem('analysisResult')
  }

  const severityWidth = result?.severityScore
    ? Math.min(result.severityScore * 20, 100)
    : 0

  return (
    <MainLayout>

      <div className="symptom-wrapper">
        <div className="symptom-header">
          <h2>AI Symptom Intelligence</h2>
          <p>Advanced AI analysis powered by machine learning</p>
        </div>

        <div className="search-container-ai">
          <input
            type="text"
            placeholder="Search symptoms (e.g., Fever, Headache)..."
            className="symptom-search"
            value={search}
            onChange={(e)=>setSearch(e.target.value)}
          />
        </div>

        <div className="symptom-grid">
          {symptomOptions
            .filter(symptom =>
              symptom.toLowerCase().includes(search.toLowerCase())
            )
            .map(symptom => (
              <button
                key={symptom}
                className={`symptom-pill ${selected.includes(symptom) ? 'active' : ''}`}
                onClick={() => toggleSymptom(symptom)}
              >
                {selected.includes(symptom) && <span className="check-icon">✓</span>}
                {symptom}
              </button>
          ))}
        </div>

        {error && <p className="error-text">{error}</p>}

        <div className="action-section">
          {!loading ? (
            <button className="primary-btn analyze-btn" onClick={handleSubmit} disabled={selected.length === 0}>
              Run AI Analysis
            </button>
          ) : (
            <AnalyzingLoader />
          )}
        </div>
      </div>

      {showModal && result && (
        <div className="modal-overlay">
          <div className="analysis-modal glass-morph fade-in">
            <button className="modal-close" onClick={()=>setShowModal(false)}>×</button>

            <div className="modal-header-ai">
              <div className="ai-badge">AI Diagnostic Report</div>
              <h3 className="modal-title">{result.condition}</h3>
            </div>

            <div className="risk-container">
              <div className={`risk-indicator ${result.risk?.toLowerCase()}`}>
                <span className="risk-label">{result.risk} Risk Level</span>
                <div className="severity-bar-bg">
                  <div 
                    className="severity-bar-fill" 
                    style={{ width: `${result.severityScore * 20 || 0}%` }}
                  ></div>
                </div>
              </div>
              <div className="confidence-meter">
                <span className="conf-val">{typeof result.confidence === 'number' ? `${(result.confidence * 100).toFixed(1)}%` : result.confidence}</span>
                <span className="conf-label"> Confidence</span>
              </div>
            </div>

            <p className="model-version">AI Model Engine v{result.modelVersion}</p>

            {result.importantFactors?.length > 0 && (
              <div className="explain-section">
                <h4>Key Contributing Factors</h4>
                <div className="factors-grid">
                  {result.importantFactors.slice(0, 3).map((factor, i) => (
                    <div key={i} className="factor-chip">
                      <span className="factor-name">{factor.feature.replace('_', ' ')}</span>
                      <span className="factor-impact">+{factor.impact}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}

            <div className="recommendation-section">
              <h4>AI Health Recommendations</h4>

              <div className={`rec-content ${showFullRec ? 'expanded' : ''}`}>
                <div className="rec-group">
                  <h5>Exercise</h5>
                  <ul>
                    {result.recommendations?.exercise?.map((i,idx)=>(
                      <li key={idx}>{i}</li>
                    ))}
                  </ul>
                </div>

                {showFullRec && (
                  <>
                    <div className="rec-group">
                      <h5>Dietary Suggestions</h5>
                      <ul>
                        {result.recommendations?.diet?.map((i, idx) => (
                          <li key={idx}>{i}</li>
                        ))}
                      </ul>
                    </div>

                    <div className="rec-group">
                      <h5>Lifestyle Changes</h5>
                      <ul>
                        {result.recommendations?.lifestyle?.map((i, idx) => (
                          <li key={idx}>{i}</li>
                        ))}
                      </ul>
                    </div>
                  </>
                )}
              </div>

              <button
                className="read-more-btn"
                onClick={()=>setShowFullRec(!showFullRec)}
              >
                {showFullRec ? 'Show Less' : 'Full Detailed Analysis'}
              </button>
            </div>

            <div className="note-section">
              <textarea
                placeholder="Add personal health observations for your records..."
                value={noteText}
                onChange={(e)=>setNoteText(e.target.value)}
              />

              <div className="modal-footer-actions">
                <button
                  className="secondary-btn"
                  onClick={handleSaveNote}
                  disabled={savingNote}
                >
                  {savingNote ? 'Archiving...' : 'Archive to Notes'}
                </button>

                <button className="primary-btn" onClick={exportPDF}>
                  Download PDF Report
                </button>
              </div>
            </div>

            <button className="primary-btn" onClick={removeReport}>
              Discard this analysis
            </button>
          </div>
        </div>
      )}

    </MainLayout>
  )
}

export default SymptomChecker