const express = require('express');
const axios = require('axios');
const app = express();

const SRS_API = process.env.SRS_URL || 'http://srs:1985';
const PORT = 3000;

app.use(express.static('public'));

// Simple proxy to fetch data from SRS API
app.get('/api/:endpoint', async (req, res) => {
    try {
        const response = await axios.get(`${SRS_API}/api/v1/${req.params.endpoint}`);
        res.json(response.data);
    } catch (error) {
        res.status(500).json({ error: 'SRS API Unreachable' });
    }
});

app.listen(PORT, () => console.log(`Monitor Dashboard active on port ${PORT}`));