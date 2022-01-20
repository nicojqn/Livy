const express = require('express')
const app = express()
const port = 3000

app.get('/', (req, res) => {
  res.send('Livy root - please read manual at github repo...')
})

app.listen(port, () => {
  console.log(`Livy is up and now listen at http://localhost:${port}`)
})
