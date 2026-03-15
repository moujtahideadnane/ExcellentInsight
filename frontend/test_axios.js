const axios = require('axios');
const FormData = require('form-data'); // using Node.js form-data for testing

const api = axios.create({
  headers: {
    'Content-Type': 'application/json',
  },
});

api.interceptors.request.use(config => {
  console.log('Sending headers:', config.headers);
  return config;
});

const fd = new FormData();
fd.append('file', Buffer.from('test'), 'test.txt');

api.post('http://localhost:8000/api/v1/upload', fd, {
  // test without content-type
}).catch(e => console.log('Error:', e.message));

api.post('http://localhost:8000/api/v1/upload', fd, {
  headers: { 'Content-Type': 'multipart/form-data' }
}).catch(e => console.log('Error:', e.message));
