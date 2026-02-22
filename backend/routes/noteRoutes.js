const express = require('express')
const router = express.Router()

const noteController = require('../controllers/noteController')
const authMiddleware = require('../middleware/authMiddleware')

router.route('/')
  .get(authMiddleware.protect, noteController.getNotes)
  .post(authMiddleware.protect, noteController.createNote)
  .delete(authMiddleware.protect, noteController.clearNotes)

router.route('/:id')
  .delete(authMiddleware.protect, noteController.deleteNote)

module.exports = router