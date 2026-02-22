const Note = require('../models/Note')
const asyncHandler = require('../utils/asyncHandler')

const createNote = asyncHandler(async (req, res) => {
  const { title, comment, text } = req.body

  if (!text) {
    res.status(400)
    throw new Error('Note text required')
  }

  const note = await Note.create({
    user: req.user._id,
    title: title || 'Untitled Note',
    comment: comment || '',
    text
  })

  res.status(201).json(note)
})

const getNotes = asyncHandler(async (req, res) => {
  const notes = await Note.find({ user: req.user._id })
    .sort({ createdAt: -1 })

  res.json(notes)
})

const deleteNote = asyncHandler(async (req, res) => {
  const note = await Note.findById(req.params.id)

  if (!note) {
    res.status(404)
    throw new Error('Note not found')
  }

  if (note.user.toString() !== req.user._id.toString()) {
    res.status(401)
    throw new Error('Not authorized')
  }

  await note.deleteOne()

  res.json({ message: 'Note removed' })
})

const clearNotes = asyncHandler(async (req, res) => {
  await Note.deleteMany({ user: req.user._id })
  res.json({ message: 'All notes cleared' })
})

module.exports = {
  createNote,
  getNotes,
  deleteNote,
  clearNotes
}