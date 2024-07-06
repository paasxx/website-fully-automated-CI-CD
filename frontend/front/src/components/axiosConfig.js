// axiosConfig.js
import axios from 'axios';

const axiosInstance = axios.create({
    baseURL: process.env.REACT_APP_BACKEND_URL, // Use the environment variable
    timeout: 100000,  // Timeout em milissegundos (por exemplo, 10 segundos)
});

export default axiosInstance;