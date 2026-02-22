const mongoose = require('mongoose')

const messageSchema = new mongoose.Schema({
  sender: {
    type: String,
    enum: ['user', 'ai'],
    required: true
  },
  text: {
    type: String,
    required: true
  }
}, { timestamps: true })

const chatSchema = new mongoose.Schema({
  user: {
    type: mongoose.Schema.Types.ObjectId,
    required: true,
    ref: 'User'
  },
  messages: [messageSchema]
}, { timestamps: true })

module.exports = mongoose.model('Chat', chatSchema)