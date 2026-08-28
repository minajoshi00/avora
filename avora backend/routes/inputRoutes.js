const router = require('express').Router();

router.post('/', (req, res) => {
  // Handle user input and context
  const userInput = req.body.input;
  res.json({ message: `Received input: ${userInput}` });
});

module.exports = router;