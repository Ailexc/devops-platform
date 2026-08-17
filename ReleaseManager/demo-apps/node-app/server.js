const express = require('express');
const os = require('os');

const app = express();
const PORT = process.env.PORT || 8080;
const APP_VERSION = process.env.APP_VERSION || '1.0.0';
const APP_NAME = process.env.APP_NAME || 'node-demo';
const ENV = process.env.ENV || 'dev';

app.get('/', (req, res) => {
  res.json({
    app: APP_NAME,
    version: APP_VERSION,
    env: ENV,
    language: 'Node.js',
    host: os.hostname(),
  });
});

app.get('/health', (req, res) => {
  res.json({ status: 'ok', app: APP_NAME, version: APP_VERSION });
});

app.get('/info', (req, res) => {
  res.json({
    app: APP_NAME,
    version: APP_VERSION,
    env: ENV,
    node_version: process.version,
    platform: os.platform(),
    arch: os.arch(),
  });
});

app.listen(PORT, () => {
  console.log(`Node.js demo app starting on :${PORT}`);
});