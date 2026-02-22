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
  'Chills','Loss of Appetite','Insomnia'
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
      console.error(err)
      setError('Prediction failed.')
    } finally {
      setLoading(false)
    }
  }

  const handleSaveNote = async () => {
    if (!noteText.trim()) {
      alert('Please write note details')
      return
    }

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
      console.error(error.response?.data || error.message)
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

  return (
    <MainLayout>

      <div className="symptom-wrapper">

        <div className="symptom-header">
          <h2>AI Symptom Intelligence</h2>
          <p>Advanced AI analysis for your health signals</p>
        </div>

        <input
          type="text"
          placeholder="Search symptoms..."
          className="symptom-search"
          value={search}
          onChange={(e)=>setSearch(e.target.value)}
        />

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
                {symptom}
              </button>
          ))}
        </div>

        {error && <p className="error-text">{error}</p>}

        <div className="action-section">
          {!loading ? (
            <button className="primary-btn analyze-btn" onClick={handleSubmit}>
              Analyze Now
            </button>
          ) : (
            <AnalyzingLoader />
          )}
        </div>

      </div>

      {showModal && result && (
        <div className="modal-overlay">
          <div className="analysis-modal fade-in">

            <button className="modal-close" onClick={()=>setShowModal(false)}>×</button>

            <h3 className="modal-title">{result.condition}</h3>

            <span className={`risk-badge ${result.risk?.toLowerCase()}`}>
              {result.risk} Risk
            </span>

            <div className="severity-bar">
              <div className={`severity-fill ${result.risk?.toLowerCase()}`}></div>
            </div>

            <p className="confidence-text">
              Confidence: <strong>{result.confidence}</strong>
            </p>

            <div className="recommendation-section">
              <h4>AI Health Recommendations</h4>

              <div className={`rec-content ${showFullRec ? 'expanded' : ''}`}>
                <h5>Exercise</h5>
                <ul>
                  {result.recommendations?.exercise?.map((i,idx)=>(
                    <li key={idx}>{i}</li>
                  ))}
                </ul>

                {showFullRec && (
                  <>
                    <h5>Diet</h5>
                    <ul>
                      {result.recommendations?.diet?.map((i,idx)=>(
                        <li key={idx}>{i}</li>
                      ))}
                    </ul>

                    <h5>Lifestyle</h5>
                    <ul>
                      {result.recommendations?.lifestyle?.map((i,idx)=>(
                        <li key={idx}>{i}</li>
                      ))}
                    </ul>
                  </>
                )}
              </div>

              <button
                className="read-more-btn"
                onClick={()=>setShowFullRec(!showFullRec)}
              >
                {showFullRec ? 'Show Less' : 'Read More'}
              </button>
            </div>

            <div className="note-section">
              <textarea
                placeholder="Add personal health notes..."
                value={noteText}
                onChange={(e)=>setNoteText(e.target.value)}
              />

              <div className="modal-actions">
                <button
                  className="secondary-btn"
                  onClick={handleSaveNote}
                  disabled={savingNote}
                >
                  {savingNote ? 'Saving...' : 'Save Note'}
                </button>

                <button
                  className="secondary-btn"
                  onClick={exportPDF}
                >
                  Download PDF
                </button>
              </div>
            </div>

            <button className="remove-report" onClick={removeReport}>
              Remove Report
            </button>

          </div>
        </div>
      )}

    </MainLayout>
  )
}

export default SymptomChecker