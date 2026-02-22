const express = require('express')
const router = express.Router()
const { body } = require('express-validator')
const { registerUser, loginUser } = require('../controllers/authController')
const validate = require('../middleware/validateMiddleware')

router.post(
  '/register',
  [
    body('name').notEmpty(),
    body('email').isEmail(),
    body('password').isLength({ min: 6 })
  ],
  validate,
  registerUser
)

router.post(
  '/login',
  [
    body('email').isEmail(),
    body('password').notEmpty()
  ],
  validate,
  loginUser
)

module.exports = router