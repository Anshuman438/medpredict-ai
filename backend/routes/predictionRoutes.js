const express = require('express')
const router = express.Router()
const { analyzeSymptoms, getUserPredictions } = require('../controllers/predictionController')
const { protect } = require('../middleware/authMiddleware')

router.post('/analyze', protect, analyzeSymptoms)
router.get('/my', protect, getUserPredictions)

module.exports = router