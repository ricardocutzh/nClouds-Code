const express = require('express');
const axios = require('axios');
const path = require('path');
const app = express();
const PORT = 3000;

app.use(express.static('public'));

// Proxy endpoint to talk to LiveGo
app.get('/api/stats', async (req, res) => {
    try {
        const livegoIp = req.query.ip;
        const response = await axios.get(`http://${livegoIp}:8090/stat/livestat`);
        res.json(response.data);
    } catch (error) {
        res.status(500).json({ error: "Could not connect to LiveGo" });
    }
});

app.get('/api/control/get', async (req, res) => {
    try {
        const { ip, room } = req.query;
        const response = await axios.get(`http://${ip}:8090/control/get?room=${room}`);
        res.json(response.data);
    } catch (error) {
        res.status(500).json({ error: "Failed to create/get room" });
    }
});

// Delete a Room
app.get('/api/control/delete', async (req, res) => {
    try {
        const { ip, room } = req.query;
        const response = await axios.get(`http://${ip}:8090/control/delete?room=${room}`);
        res.json(response.data);
    } catch (error) {
        res.status(500).json({ error: "Failed to delete room" });
    }
});

app.listen(PORT, () => console.log(`Dashboard running on http://localhost:${PORT}`));