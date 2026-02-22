import { useState, useEffect } from 'react'
import MainLayout from '../layouts/MainLayout'
import api from '../services/api'

const pastelColors = [
  '#E0F2FE',
  '#FCE7F3',
  '#ECFDF5',
  '#FEF9C3',
  '#F3E8FF',
  '#FFE4E6',
  '#E9F5FF',
  '#FFF7ED'
]

function Notes() {
  const [notes, setNotes] = useState([])
  const [title, setTitle] = useState('')
  const [comment, setComment] = useState('')
  const [text, setText] = useState('')
  const [selectedNote, setSelectedNote] = useState(null)

  useEffect(() => {
    fetchNotes()
  }, [])

  const fetchNotes = async () => {
    try {
      const { data } = await api.get('/notes')
      setNotes(data)
    } catch (error) {
      console.error(error)
    }
  }

  const addNote = async () => {
    if (!text.trim()) return

    try {
      const { data } = await api.post('/notes', {
        title: title || 'Untitled Note',
        comment: comment || '',
        text
      })

      setNotes(prev => [data, ...prev])
      setTitle('')
      setComment('')
      setText('')
    } catch (error) {
      console.error(error.response?.data || error.message)
      alert('Failed to add note')
    }
  }

  const removeNote = async (id) => {
    try {
      await api.delete(`/notes/${id}`)
      setNotes(notes.filter(note => note._id !== id))
    } catch (error) {
      console.error(error)
    }
  }

  const clearAll = async () => {
    try {
      await api.delete('/notes')
      setNotes([])
    } catch (error) {
      console.error(error)
    }
  }

  const truncateText = (text, limit = 140) => {
    if (text.length <= limit) return text
    return text.substring(0, limit) + '...'
  }

  return (
    <MainLayout>
      <div className="notes-wrapper">

        <h2 className="notes-title">Wellness Notes</h2>

        {/* Add Note Section */}
        <div className="add-note-card">
          <input
            type="text"
            placeholder="Note Title"
            value={title}
            onChange={(e) => setTitle(e.target.value)}
          />

          <input
            type="text"
            placeholder="Short Comment (optional)"
            value={comment}
            onChange={(e) => setComment(e.target.value)}
          />

          <textarea
            placeholder="Write your note..."
            value={text}
            onChange={(e) => setText(e.target.value)}
          />

          <button className="primary-btn" onClick={addNote}>
            Add Note
          </button>
        </div>

        {notes.length > 0 && (
          <div className="clear-all-container">
            <button className="danger-btn" onClick={clearAll}>
              Clear All Notes
            </button>
          </div>
        )}

        {/* Notes Grid */}
        <div className="notes-grid">
          {notes.map((note, index) => (
            <div
              key={note._id}
              className="note-card-modern"
              style={{
                backgroundColor:
                  pastelColors[index % pastelColors.length]
              }}
            >
              <div className="note-content">
                <h3 className="note-title">{note.title}</h3>

                {note.comment && (
                  <p className="note-comment">{note.comment}</p>
                )}

                <p className="note-preview">
                  {truncateText(note.text)}
                </p>

                {note.text.length > 140 && (
                  <button
                    className="read-more-btn-modern"
                    onClick={() => setSelectedNote(note)}
                  >
                    Read More →
                  </button>
                )}
              </div>

              <button
                className="remove-btn remove-bottom"
                onClick={() => removeNote(note._id)}
              >
                Remove
              </button>
            </div>
          ))}
        </div>
      </div>

      {/* Modal */}
      {selectedNote && (
        <div
          className="modal-overlay"
          onClick={() => setSelectedNote(null)}
        >
          <div
            className="modal-content-modern"
            onClick={(e) => e.stopPropagation()}
          >
            <h2>{selectedNote.title}</h2>

            {selectedNote.comment && (
              <p>{selectedNote.comment}</p>
            )}

            <div className="modal-text">
              {selectedNote.text}
            </div>

            <button
              className="primary-btn"
              onClick={() => setSelectedNote(null)}
            >
              Close
            </button>
          </div>
        </div>
      )}

    </MainLayout>
  )
}

export default Notes