/* Shared, deterministic filtering for the browser and regression checks. */
(function (root) {
  'use strict';
  function normalizeName(value) {
    return String(value || '').normalize('NFD').replace(/[\u0300-\u036f]/g, '')
      .replace(/[đĐ]/g, 'd').toLowerCase().trim().replace(/\s+/g, ' ');
  }
  function filterTrips(trips, operatorName = '', interval = '') {
    const query = normalizeName(operatorName);
    const bounds = interval ? interval.split('-').map(Number) : null;
    return trips.filter(trip => {
      if (query && !normalizeName(trip.operator).includes(query)) return false;
      if (!bounds) return true;
      const clock = trip.departure.slice(11, 16).split(':').map(Number);
      const minutes = clock[0] * 60 + clock[1];
      return minutes >= bounds[0] && minutes < bounds[1];
    });
  }
  const api = { normalizeName, filterTrips };
  if (typeof module === 'object' && module.exports) module.exports = api;
  else root.ViVuTripFilters = api;
})(typeof window === 'undefined' ? globalThis : window);
