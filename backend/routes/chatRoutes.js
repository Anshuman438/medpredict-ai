const express = require('express')
const router = express.Router()
const { sendMessage, getChatHistory } = require('../controllers/chatController')
const { protect } = require('../middleware/authMiddleware')

router.post('/', protect, sendMessage)
router.get('/', protect, getChatHistory)

module.exports = router