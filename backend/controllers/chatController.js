const Chat = require('../models/Chat')
const asyncHandler = require('../utils/asyncHandler')

const sendMessage = asyncHandler(async (req, res) => {
  const { text } = req.body

  if (!text) {
    res.status(400)
    throw new Error('Message text required')
  }

  let chat = await Chat.findOne({ user: req.user._id })

  if (!chat) {
    chat = await Chat.create({
      user: req.user._id,
      messages: []
    })
  }

  chat.messages.push({ sender: 'user', text })

  const aiResponse = {
    sender: 'ai',
    text: 'Based on your message, maintain hydration and monitor your health regularly.'
  }

  chat.messages.push(aiResponse)

  await chat.save()

  res.status(201).json(chat)
})

const getChatHistory = asyncHandler(async (req, res) => {
  const chat = await Chat.findOne({ user: req.user._id })

  if (!chat) {
    return res.json({ messages: [] })
  }

  res.json(chat)
})

module.exports = { sendMessage, getChatHistory }