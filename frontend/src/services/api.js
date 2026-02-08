/**
 * API Service for M3 Timetable System
 * 
 * Centralized API calls to Django backend
 * 
 * Author: Frontend Team (Bhuvanesh, Akshitha)
 * Sprint: 1
 */

import axios from 'axios';

const API_BASE_URL = 'http://localhost:8000/api';

// Create axios instance with default config
const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add request interceptor to attach token
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('access_token');
    if (token) {
      config.headers['Authorization'] = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Core Data APIs
export const teacherAPI = {
  getAll: () => api.get('/teachers/'),
  getById: (id) => api.get(`/teachers/${id}/`),
  create: (data) => api.post('/teachers/', data),
  update: (id, data) => api.put(`/teachers/${id}/`, data),
  delete: (id) => api.delete(`/teachers/${id}/`),
  byDepartment: (dept) => api.get(`/teachers/by_department/?department=${dept}`),
};

export const courseAPI = {
  getAll: () => api.get('/courses/'),
  getById: (id) => api.get(`/courses/${id}/`),
  create: (data) => api.post('/courses/', data),
  update: (id, data) => api.put(`/courses/${id}/`, data),
  delete: (id) => api.delete(`/courses/${id}/`),
  byYear: (year) => api.get(`/courses/by_year/?year=${year}`),
  bySemester: (sem) => api.get(`/courses/by_semester/?semester=${sem}`),
};

export const roomAPI = {
  getAll: () => api.get('/rooms/'),
  getById: (id) => api.get(`/rooms/${id}/`),
  create: (data) => api.post('/rooms/', data),
  update: (id, data) => api.put(`/rooms/${id}/`, data),
  delete: (id) => api.delete(`/rooms/${id}/`),
  byType: (type) => api.get(`/rooms/by_type/?type=${type}`),
};

export const sectionAPI = {
  getAll: () => api.get('/sections/'),
  getById: (id) => api.get(`/sections/${id}/`),
  create: (data) => api.post('/sections/', data),
  update: (id, data) => api.put(`/sections/${id}/`, data),
  delete: (id) => api.delete(`/sections/${id}/`),
  byYear: (year) => api.get(`/sections/by_year/?year=${year}`),
};

export const timeslotAPI = {
  getAll: () => api.get('/timeslots/'),
  getById: (id) => api.get(`/timeslots/${id}/`),
  byDay: (day) => api.get(`/timeslots/by_day/?day=${day}`),
};

export const scheduleAPI = {
  getAll: () => api.get('/schedules/'),
  getById: (id) => api.get(`/schedules/${id}/`),
  create: (data) => api.post('/schedules/', data),
  delete: (id) => api.delete(`/schedules/${id}/`),
  getEntries: (id) => api.get(`/schedules/${id}/entries/`),
  getConflicts: (id) => api.get(`/schedules/${id}/conflicts/`),
};

// Scheduler APIs
export const schedulerAPI = {
  generate: (data) => api.post('/scheduler/generate', data),
  getWorkload: (scheduleId) => api.get(`/scheduler/analytics/workload?schedule_id=${scheduleId}`),
  getRoomUtilization: (scheduleId) => api.get(`/scheduler/analytics/rooms?schedule_id=${scheduleId}`),
  getTimetable: (scheduleId, section = null, teacher = null) => {
    let url = `/scheduler/timetable?schedule_id=${scheduleId}`;
    if (section) url += `&section=${section}`;
    if (teacher) url += `&teacher=${teacher}`;
    return api.get(url);
  },
};

export default api;
