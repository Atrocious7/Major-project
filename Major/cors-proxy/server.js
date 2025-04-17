// filepath: /c:/Users/tarun/OneDrive/Desktop/CODES/Major/cors-proxy/server.js
const express = require('express');
const { createProxyMiddleware } = require('http-proxy-middleware');

const app = express();

app.use('/api', createProxyMiddleware({
    target: 'https://generativelanguage.googleapis.com',
    changeOrigin: true,
    pathRewrite: {
        '^/api': '', // remove /api prefix
    },
    onProxyReq: (proxyReq, req, res) => {
        proxyReq.setHeader('origin', 'http://127.0.0.1:5000');
    },
}));

app.listen(3000, () => {
    console.log('CORS Proxy Server running on http://localhost:3000');
});